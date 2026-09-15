from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import RequestFactory, SimpleTestCase, override_settings
from django.urls import resolve

from lms_modules.github_sync import views


@override_settings(GITHUB_OAUTH_REDIRECT_URI="", SITE_URL="https://qa.example.com")
class IntegratedCallbackTests(SimpleTestCase):
    def request(self, state="student-state"):
        request = RequestFactory().get('/github/callback/', {'state': state, 'code': 'test-code'})
        request.user = SimpleNamespace(is_authenticated=True, id=1)
        request.session = {'github_oauth_state': 'student-state', 'github_oauth_state_tutor': 'tutor-state'}
        return request

    def test_uses_site_url_instead_of_request_host(self):
        self.assertEqual(views._callback_uri(self.request()), 'https://qa.example.com/github/callback/')

    @override_settings(GITHUB_OAUTH_REDIRECT_URI='https://oauth.example.com/github/callback/')
    def test_explicit_callback_takes_priority(self):
        self.assertEqual(views._callback_uri(self.request()), 'https://oauth.example.com/github/callback/')

    @override_settings(SITE_URL='')
    def test_blank_configuration_preserves_request_fallback(self):
        self.assertEqual(views._callback_uri(self.request()), 'http://testserver/github/callback/')

    @override_settings(GITHUB_OAUTH_REDIRECT_URI='javascript:invalid')
    def test_invalid_callback_fails_closed(self):
        with self.assertRaises(ImproperlyConfigured):
            views._callback_uri(self.request())

    def test_legacy_tutor_callback_remains_routable(self):
        self.assertIs(resolve('/github/callback/tutor/').func, views.callback)

    @patch.object(views.services, 'enabled', return_value=True)
    def test_simultaneous_states_dispatch_by_matching_state(self, enabled):
        request = self.request()
        with patch.object(views, '_finish_student', return_value=HttpResponse('student')) as student, patch.object(views, '_finish_tutor') as tutor:
            self.assertEqual(views.callback(request).content, b'student')
            student.assert_called_once()
            tutor.assert_not_called()
        self.assertNotIn('github_oauth_state', request.session)
        self.assertEqual(request.session['github_oauth_state_tutor'], 'tutor-state')

    @patch.object(views.services, 'enabled', return_value=True)
    @patch.object(views.messages, 'error')
    def test_wrong_state_never_exchanges_code(self, error, enabled):
        with patch.object(views.oauth, 'exchange_code') as exchange:
            response = views.callback(self.request('wrong-state'))
            self.assertEqual(response.status_code, 302)
            exchange.assert_not_called()
