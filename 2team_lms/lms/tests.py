from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.db import connections, router
from django.template.loader import get_template
from django.test import SimpleTestCase, TestCase, RequestFactory
from django.urls import resolve, reverse
from django.utils import timezone

from lms_modules import transaction
from lms_modules.core.models import Assignment, Submission, SubmissionFile, Evaluation
from lms_modules.accounts_client.models import AxUserLogin
from lms_modules.notifications import slack
from lms_modules.github_sync.models import StudentGithubAccount
from lms_modules.student.views_dashboard import dashboard
from lms_modules.tutor.views_dashboard import dashboard as tutor_dashboard


class IntegrationContracts(SimpleTestCase):
    def test_core_login_and_lms_urls_are_separate(self):
        self.assertEqual(reverse('accounts:login'), '/accounts/login/')
        self.assertEqual(reverse('lms:student:dashboard'), '/lms/dashboard/')
        self.assertEqual(reverse('lms:tutor:dashboard'), '/lms/tutor/')
        self.assertEqual(reverse('lms:github_sync:callback'), '/lms/github/callback/')
        self.assertEqual(reverse('lms:lecture-list'), '/lms/lecture/')

    def test_all_lms_templates_compile(self):
        for app in apps.get_app_configs():
            if not app.name.startswith('lms_modules.'):
                continue
            root = Path(app.path) / 'templates'
            for path in root.rglob('*.html'):
                with self.subTest(template=str(path)):
                    get_template(path.relative_to(root).as_posix())

    def test_core_base_template_is_not_shadowed(self):
        self.assertNotIn('lms_modules', get_template('base.html').origin.name)
        self.assertIn('lms_modules', get_template('lms_ui/base.html').origin.name)

    def test_routing_isolated(self):
        self.assertEqual(router.db_for_read(Assignment), 'assignment_lms')
        self.assertEqual(router.db_for_write(Submission), 'assignment_lms')
        self.assertEqual(router.db_for_read(AxUserLogin), 'default')
        with self.assertRaises(RuntimeError):
            router.db_for_write(AxUserLogin)
        self.assertFalse(router.allow_migrate('default', 'core'))
        self.assertFalse(router.allow_migrate('assignment_lms', 'accounts'))
        self.assertTrue(router.allow_migrate('assignment_lms', 'github_sync'))

    def test_anonymous_lms_access_redirects_to_core_login(self):
        for url in ('/lms/', '/lms/dashboard/', '/lms/tutor/', '/lms/lecture/', '/lms/assignments/'):
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302)
                self.assertTrue(response.url.startswith('/accounts/login/'))

    def test_slack_delegates_to_core_and_failure_does_not_escape(self):
        with patch('notifications.slack.send_slack_dm_ax', return_value=True) as send:
            self.assertTrue(slack.send_slack_dm_ax(31, 'title', 'body', '/lms/'))
            send.assert_called_once_with(31, 'title', 'body', '/lms/')
        with patch('notifications.slack.send_slack_dm_ax', side_effect=RuntimeError('offline')):
            self.assertFalse(slack.send_slack_dm_ax(31))


class DomainDatabaseTests(TestCase):
    databases = {'default', 'assignment_lms'}

    def assignment(self):
        return Assignment.objects.create(title='QA assignment', due_at=timezone.now()+timedelta(days=1), created_by=31)

    def test_domain_tables_only_created_in_lms_database(self):
        self.assertNotIn('assignment', connections['default'].introspection.table_names())
        self.assertIn('assignment', connections['assignment_lms'].introspection.table_names())
        self.assertNotIn('accounts_user', connections['assignment_lms'].introspection.table_names())

    def test_evaluation_sync_preserves_raw_score_in_lms_database(self):
        submission = Submission.objects.create(assignment=self.assignment(), student_id=31)
        Evaluation.objects.create(submission=submission, score=100, feedback='QA')
        submission.refresh_from_db()
        self.assertEqual(submission.final_score, 100)
        self.assertTrue(submission.is_locked)
        self.assertEqual(submission._state.db, 'assignment_lms')

    def test_rollback_removes_lms_write_and_discards_callback(self):
        called = []
        with self.assertRaises(ValueError):
            with transaction.atomic():
                self.assignment()
                transaction.on_commit(lambda: called.append(True))
                raise ValueError('rollback')
        self.assertEqual(Assignment.objects.count(), 0)
        self.assertEqual(called, [])

    def test_github_callback_uses_lms_commit(self):
        submission = Submission.objects.create(assignment=self.assignment(), student_id=31)
        with patch('lms_modules.github_sync.services.enabled', return_value=True), patch('lms_modules.github_sync.services.enqueue') as enqueue, patch('lms_modules.github_sync.services.try_sync_now'):
            with self.captureOnCommitCallbacks(using='assignment_lms', execute=True) as callbacks:
                SubmissionFile.objects.create(submission=submission, kind='PY', file_url='/lms-media/qa.py', file_name='qa.py', file_size=1)
                enqueue.assert_not_called()
            self.assertEqual(len(callbacks), 1)
            enqueue.assert_called_once()

    def test_student_dashboard_renders_with_core_user_contract(self):
        request = RequestFactory().get('/lms/dashboard/')
        request.resolver_match = resolve('/lms/dashboard/')
        request.user = SimpleNamespace(id=31, is_authenticated=True)
        with patch('lms_modules.accounts_client.services.is_student', return_value=True), patch('lms_modules.accounts_client.services.is_tutor', return_value=False), patch('lms_modules.accounts_client.services.get_user_team', return_value=None):
            response = dashboard(request)
        self.assertEqual(response.status_code, 200)

    def post_request(self, url, data):
        from django.contrib.messages.storage.fallback import FallbackStorage
        request = RequestFactory().post(url, data)
        request.user = SimpleNamespace(id=31, is_authenticated=True)
        request.session = {}
        request._messages = FallbackStorage(request)
        request.resolver_match = resolve(url)
        return request

    def test_submit_then_resubmit_uses_existing_core_user_id(self):
        from lms_modules.student.views_submit import assignment_submit
        from lms_modules.student.views_result import resubmit
        assignment = self.assignment()
        request = self.post_request(f'/lms/assignments/{assignment.pk}/submit/', {'description':'first', 'links':['https://example.com/first.py']})
        with patch('lms_modules.accounts_client.services.is_student', return_value=True), patch('lms_modules.student.views_submit.notify_dm_ax'):
            response = assignment_submit(request, assignment.pk)
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(assignment=assignment, student_id=31)
        self.assertEqual(submission.files.count(), 1)
        request = self.post_request(f'/lms/submissions/{submission.pk}/resubmit/', {'description':'second','links':['https://example.com/second.py']})
        with patch('lms_modules.accounts_client.services.is_student', return_value=True), patch('lms_modules.accounts_client.services.get_user_team', return_value=None):
            response = resubmit(request, submission.pk)
        self.assertEqual(response.status_code, 302)
        submission.refresh_from_db()
        self.assertEqual(submission.description, 'second')
        self.assertEqual(submission.files.get().file_url, 'https://example.com/second.py')
        self.assertEqual(Submission.objects.count(), 1)

    def test_tutor_evaluation_saves_raw_score_and_locks_resubmission(self):
        from lms_modules.tutor.views_review import submission_review
        from lms_modules.student.views_result import resubmit
        submission = Submission.objects.create(assignment=self.assignment(), student_id=31)
        request = self.post_request(f'/lms/tutor/submissions/{submission.pk}/review/', {'score':100,'feedback':'Good'})
        with patch('lms_modules.accounts_client.services.is_tutor', return_value=True), patch('lms_modules.tutor.views_review.notify_dm_ax_many'):
            response = submission_review(request, submission.pk)
        self.assertEqual(response.status_code, 302)
        submission.refresh_from_db()
        self.assertEqual(submission.final_score,100)
        self.assertTrue(submission.is_locked)
        request = self.post_request(f'/lms/submissions/{submission.pk}/resubmit/', {'description':'blocked','links':['https://example.com/new.py']})
        with patch('lms_modules.accounts_client.services.is_student', return_value=True), patch('lms_modules.accounts_client.services.get_user_team', return_value=None):
            response = resubmit(request, submission.pk)
        self.assertEqual(response.status_code,302)
        submission.refresh_from_db()
        self.assertNotEqual(submission.description,'blocked')

    def test_assignment_delete_and_restore_preserve_submissions(self):
        from lms_modules.tutor.views_manage import assignment_delete, assignment_restore
        from django.urls import reverse
        assignment = self.assignment()
        submission = Submission.objects.create(assignment=assignment, student_id=31)
        with patch('lms_modules.accounts_client.services.is_tutor', return_value=True):
            req = self.post_request(reverse('lms:tutor:assignment-delete', args=[assignment.pk]), {'confirm':'yes'})
            response = assignment_delete(req, assignment.pk)
            self.assertEqual(response.status_code, 302)
            from django.contrib.messages import get_messages
            self.assertIn('csrfmiddlewaretoken', str(list(get_messages(req))[0]))
            self.assertFalse(Assignment.objects.filter(pk=assignment.pk).exists())
            self.assertTrue(Submission.objects.filter(pk=submission.pk).exists())
            req = self.post_request(reverse('lms:tutor:assignment-restore', args=[assignment.pk]), {})
            response = assignment_restore(req, assignment.pk)
            self.assertEqual(response.status_code, 302)
            self.assertTrue(Assignment.objects.filter(pk=assignment.pk).exists())
