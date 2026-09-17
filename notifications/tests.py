from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from notifications.models import Notification, SlackIdentity
from notifications.services import (
    EMAIL_CAPABLE_CATEGORIES,
    announce,
    delete_all_notifications,
    delete_notification,
    link_slack_user,
    mark_all_read,
    mark_read,
    notify_users,
    sync_slack_users,
    unread_count,
)


class NotifyUsersTests(TestCase):
    def setUp(self):
        self.students = [
            User.objects.create_user(
                email=f"notify-student-{index}@example.com",
                password="strong-test-password",
                first_name=f"학생{index}",
                role=User.Role.STUDENT,
                approval_status=User.ApprovalStatus.APPROVED,
            )
            for index in range(1, 3)
        ]

    def test_notify_users_creates_one_row_per_recipient(self):
        notify_users(
            self.students,
            category=Notification.Category.NOTICE,
            title="새 공지가 등록되었습니다",
            message="점검 안내",
        )

        self.assertEqual(Notification.objects.count(), 2)
        self.assertEqual(unread_count(self.students[0]), 1)

    def test_mark_read_only_affects_that_users_notification(self):
        notify_users(self.students, category=Notification.Category.NOTICE, title="공지")
        target = Notification.objects.get(recipient=self.students[0])

        mark_read(user=self.students[0], notification_id=target.pk)

        self.assertEqual(unread_count(self.students[0]), 0)
        self.assertEqual(unread_count(self.students[1]), 1)

    def test_mark_all_read_clears_every_unread_notification(self):
        notify_users(self.students, category=Notification.Category.NOTICE, title="공지")
        notify_users(self.students, category=Notification.Category.NOTICE, title="공지2")

        mark_all_read(self.students[0])

        self.assertEqual(unread_count(self.students[0]), 0)

    def test_delete_notification_only_removes_that_recipients_row(self):
        notify_users(self.students, category=Notification.Category.NOTICE, title="공지")
        target = Notification.objects.get(recipient=self.students[0])

        delete_notification(user=self.students[0], notification_id=target.pk)

        self.assertEqual(Notification.objects.filter(recipient=self.students[0]).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.students[1]).count(), 1)

    def test_delete_notification_ignores_another_users_notification(self):
        notify_users(self.students, category=Notification.Category.NOTICE, title="공지")
        other_notification = Notification.objects.get(recipient=self.students[1])

        delete_notification(user=self.students[0], notification_id=other_notification.pk)

        self.assertTrue(Notification.objects.filter(pk=other_notification.pk).exists())

    def test_delete_all_notifications_clears_only_that_users_rows(self):
        notify_users(self.students, category=Notification.Category.NOTICE, title="공지")
        notify_users(self.students, category=Notification.Category.NOTICE, title="공지2")

        delete_all_notifications(self.students[0])

        self.assertEqual(Notification.objects.filter(recipient=self.students[0]).count(), 0)
        self.assertEqual(Notification.objects.filter(recipient=self.students[1]).count(), 2)


class NotificationApiTests(TestCase):
    def setUp(self):
        self.student = User.objects.create_user(
            email="notify-api-student@example.com",
            password="strong-test-password",
            first_name="학생",
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
        )

    def test_summary_lists_newest_first_with_unread_count(self):
        notify_users([self.student], category=Notification.Category.NOTICE, title="첫 번째")
        notify_users([self.student], category=Notification.Category.NOTICE, title="두 번째")
        self.client.force_login(self.student)

        response = self.client.get(reverse("notifications:summary"))

        data = response.json()
        self.assertEqual(data["unread_count"], 2)
        self.assertEqual(data["items"][0]["title"], "두 번째")
        self.assertEqual(data["items"][1]["title"], "첫 번째")

    def test_mark_read_endpoint_requires_post(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("notifications:summary"))

        self.assertEqual(response.status_code, 200)

    def test_mark_read_endpoint_updates_unread_count(self):
        notify_users([self.student], category=Notification.Category.NOTICE, title="공지")
        notification = Notification.objects.get(recipient=self.student)
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("notifications:mark-read", kwargs={"notification_id": notification.pk})
        )

        self.assertEqual(response.json()["unread_count"], 0)

    def test_a_student_cannot_mark_another_students_notification_read(self):
        other = User.objects.create_user(
            email="notify-other-student@example.com",
            password="strong-test-password",
            first_name="다른학생",
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
        )
        notify_users([other], category=Notification.Category.NOTICE, title="공지")
        notification = Notification.objects.get(recipient=other)
        self.client.force_login(self.student)

        self.client.post(
            reverse("notifications:mark-read", kwargs={"notification_id": notification.pk})
        )

        self.assertEqual(unread_count(other), 1)

    def test_anonymous_user_cannot_read_summary(self):
        response = self.client.get(reverse("notifications:summary"))

        self.assertNotEqual(response.status_code, 200)

    def test_delete_endpoint_removes_the_notification(self):
        notify_users([self.student], category=Notification.Category.NOTICE, title="공지")
        notification = Notification.objects.get(recipient=self.student)
        self.client.force_login(self.student)

        response = self.client.post(
            reverse("notifications:delete", kwargs={"notification_id": notification.pk})
        )

        self.assertEqual(response.json()["unread_count"], 0)
        self.assertFalse(Notification.objects.filter(pk=notification.pk).exists())

    def test_a_student_cannot_delete_another_students_notification(self):
        other = User.objects.create_user(
            email="notify-delete-other@example.com",
            password="strong-test-password",
            first_name="다른학생",
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
        )
        notify_users([other], category=Notification.Category.NOTICE, title="공지")
        notification = Notification.objects.get(recipient=other)
        self.client.force_login(self.student)

        self.client.post(
            reverse("notifications:delete", kwargs={"notification_id": notification.pk})
        )

        self.assertTrue(Notification.objects.filter(pk=notification.pk).exists())

    def test_delete_all_endpoint_clears_every_notification(self):
        notify_users([self.student], category=Notification.Category.NOTICE, title="공지")
        notify_users([self.student], category=Notification.Category.NOTICE, title="공지2")
        self.client.force_login(self.student)

        response = self.client.post(reverse("notifications:delete-all"))

        self.assertEqual(response.json()["unread_count"], 0)
        self.assertEqual(Notification.objects.filter(recipient=self.student).count(), 0)


class AnnounceTests(TestCase):
    """알림과 메일은 한 사건에서 함께 나가야 한다 - 따로 챙기다 결과 공개가 어긋났었다."""

    def setUp(self):
        self.students = [
            User.objects.create_user(
                email=f"announce-{index}@example.com",
                password="strong-test-password",
                role=User.Role.STUDENT,
                approval_status=User.ApprovalStatus.APPROVED,
            )
            for index in range(3)
        ]

    def test_bell_notification_always_lands_even_when_mail_is_muted(self):
        muted = self.students[0]
        muted.muted_email_categories = [Notification.Category.RESULTS_PUBLISHED.value]
        muted.save(update_fields=["muted_email_categories"])
        mailed = []

        announce(
            self.students,
            category=Notification.Category.RESULTS_PUBLISHED,
            title="평가 결과가 공개되었습니다",
            email_sender=lambda users: mailed.extend(user.email for user in users),
        )

        self.assertEqual(
            Notification.objects.filter(category=Notification.Category.RESULTS_PUBLISHED).count(),
            3,
        )
        self.assertNotIn(muted.email, mailed)
        self.assertIn(self.students[1].email, mailed)

    def test_categories_without_a_mail_template_only_ring_the_bell(self):
        announce(
            self.students,
            category=Notification.Category.TEAM_CREATED,
            title="팀이 배정되었습니다",
        )

        self.assertEqual(
            Notification.objects.filter(category=Notification.Category.TEAM_CREATED).count(), 3
        )
        self.assertNotIn(Notification.Category.TEAM_CREATED, EMAIL_CAPABLE_CATEGORIES)

    def test_mypage_switches_mail_off_without_touching_the_bell(self):
        student = self.students[0]
        self.client.force_login(student)

        self.client.post(
            reverse("accounts:email_preferences"),
            {"email_categories": [Notification.Category.NOTICE.value]},
        )

        student.refresh_from_db()
        self.assertFalse(student.wants_email(Notification.Category.SUBMISSION_REMINDER))
        self.assertTrue(student.wants_email(Notification.Category.NOTICE))


class SlackDirectMessageTests(TestCase):
    @patch.dict(
        "os.environ",
        {
            "SLACK_TARGET_ENV": "test",
            "SLACK_TEST_BOT_TOKEN": "xoxb-test-token",
            "SLACK_PROD_BOT_TOKEN": "xoxb-production-token",
        },
        clear=True,
    )
    @patch("notifications.slack.requests.post")
    def test_send_slack_dm_opens_user_dm_and_posts_message(self, mock_post):
        from notifications.slack import send_slack_dm

        open_response = mock_post.return_value
        open_response.raise_for_status.return_value = None
        open_response.json.side_effect = [
            {"ok": True, "channel": {"id": "D123"}},
            {"ok": True, "ts": "123.456"},
        ]

        self.assertTrue(
            send_slack_dm(
                slack_user_id="U123",
                title="테스트 알림",
                message="테스트 메시지",
            )
        )

        self.assertEqual(mock_post.call_count, 2)
        self.assertIn("conversations.open", mock_post.call_args_list[0].args[0])
        self.assertEqual(
            mock_post.call_args_list[0].kwargs["headers"]["Authorization"],
            "Bearer xoxb-test-token",
        )
        self.assertEqual(mock_post.call_args_list[0].kwargs["json"], {"users": "U123"})
        self.assertIn("chat.postMessage", mock_post.call_args_list[1].args[0])
        self.assertEqual(mock_post.call_args_list[1].kwargs["json"]["channel"], "D123")

    @patch.dict("os.environ", {}, clear=True)
    def test_send_slack_dm_returns_false_without_bot_token(self):
        from notifications.slack import send_slack_dm

        self.assertFalse(send_slack_dm(slack_user_id="U123", title="테스트"))

    @patch.dict(
        "os.environ",
        {
            "SLACK_TARGET_ENV": "production",
            "SLACK_TEST_WEBHOOK_URL": "https://hooks.slack.com/services/test/value",
            "SLACK_PROD_WEBHOOK_URL": "https://hooks.slack.com/services/production/value",
        },
        clear=True,
    )
    @patch("notifications.slack.requests.post")
    def test_send_slack_message_uses_production_webhook_when_selected(self, mock_post):
        from notifications.slack import send_slack_message

        mock_post.return_value.raise_for_status.return_value = None

        self.assertTrue(send_slack_message(title="운영 알림"))
        self.assertEqual(
            mock_post.call_args.args[0],
            "https://hooks.slack.com/services/production/value",
        )


class SlackSyncTests(TestCase):
    @patch("notifications.services.fetch_slack_users")
    def test_sync_preserves_manual_link_when_email_does_not_match(self, mock_fetch):
        user = User.objects.create_user(
            email="project-user@example.com",
            password="strong-test-password",
            first_name="프로젝트 사용자",
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
        )
        identity = SlackIdentity.objects.create(
            slack_user_id="U_MANUAL",
            slack_email="old-slack@example.com",
            slack_display_name="수동 연결 사용자",
            is_active=True,
        )
        link_slack_user(user=user, slack_user_id=identity.slack_user_id)

        mock_fetch.return_value = [
            {
                "slack_user_id": "U_MANUAL",
                "email": "different-slack@example.com",
                "display_name": "수동 연결 사용자",
                "is_active": True,
            }
        ]

        sync_slack_users()

        identity.refresh_from_db()
        self.assertEqual(identity.user_id, user.pk)
        self.assertEqual(identity.slack_email, "different-slack@example.com")
