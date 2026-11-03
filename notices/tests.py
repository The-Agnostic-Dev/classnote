from datetime import date, datetime, timedelta
from datetime import timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from reports.models import SchoolClass

from .forms import NoticeForm
from .models import Notice
from .services import posted_label


class NoticeTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.teacher = get_user_model().objects.create_user("teacher", password="pass-12345", first_name="Ada")
        cls.jss1 = SchoolClass.objects.create(name="JSS 1A")
        cls.jss2 = SchoolClass.objects.create(name="JSS 2B")

    def setUp(self):
        cache.clear()

    def make_notice(self, title, **extra):
        classes = extra.pop("classes", [])
        notice = Notice.objects.create(title=title, body="Details inside.", author=self.teacher, **extra)
        notice.audience.set(classes)
        return notice

    def test_posted_label_uses_local_date_after_midnight(self):
        with timezone.override("Africa/Lagos"):
            late_night = datetime(2026, 11, 2, 23, 30, tzinfo=dt_timezone.utc)
            notice = self.make_notice("Late night notice", published_at=late_night)
            self.assertEqual(posted_label(notice.published_at, today=date(2026, 11, 3)), "Today")

            previous_day = datetime(2026, 11, 2, 12, 0, tzinfo=dt_timezone.utc)
            prev_notice = self.make_notice("Previous day notice", published_at=previous_day)
            self.assertEqual(posted_label(prev_notice.published_at, today=date(2026, 11, 3)), "Yesterday")


class BoardTests(NoticeTestCase):
    def test_board_lists_current_notices(self):
        self.make_notice("Sports day")
        response = self.client.get(reverse("notices:board"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sports day")

    def test_expired_notices_are_hidden(self):
        self.make_notice("Old news", expires_on=timezone.localdate() - timedelta(days=1))
        self.make_notice("Still running", expires_on=timezone.localdate() + timedelta(days=3))
        response = self.client.get(reverse("notices:board"))
        self.assertNotContains(response, "Old news")
        self.assertContains(response, "Still running")

    def test_notice_expiring_today_is_visible(self):
        self.make_notice("Expires today", expires_on=timezone.localdate())
        response = self.client.get(reverse("notices:board"))
        self.assertContains(response, "Expires today")

    def test_class_filter_hides_other_classes(self):
        self.make_notice("JSS 1A trip", classes=[self.jss1])
        self.make_notice("JSS 2B trip", classes=[self.jss2])
        response = self.client.get(reverse("notices:board"), {"class": self.jss1.pk})
        self.assertContains(response, "JSS 1A trip")
        self.assertNotContains(response, "JSS 2B trip")

    def test_detail_page(self):
        notice = self.make_notice("Uniform reminder")
        response = self.client.get(notice.get_absolute_url())
        self.assertContains(response, "Uniform reminder")


class PostedLabelTests(TestCase):
    def test_labels_recent_days(self):
        today = date(2026, 3, 18)
        noon = lambda d: datetime(d.year, d.month, d.day, 12, 0, tzinfo=dt_timezone.utc)  # noqa: E731
        self.assertEqual(posted_label(noon(today), today), "Today")
        self.assertEqual(posted_label(noon(today - timedelta(days=1)), today), "Yesterday")
        self.assertEqual(posted_label(noon(today - timedelta(days=3)), today), "3 days ago")
        self.assertIsNone(posted_label(noon(today - timedelta(days=10)), today))


class TeacherNoticeTests(NoticeTestCase):
    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("notices:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_teacher_can_post_a_notice(self):
        self.client.force_login(self.teacher)
        self.client.get(reverse("notices:board"))
        response = self.client.post(
            reverse("notices:create"),
            {"title": "Choir practice", "body": "Hall, 3 pm.", "audience": [self.jss1.pk]},
        )
        self.assertRedirects(response, reverse("notices:dashboard"))
        notice = Notice.objects.get(title="Choir practice")
        self.assertEqual(notice.author, self.teacher)
        self.assertEqual(list(notice.audience.all()), [self.jss1])
        self.assertContains(self.client.get(reverse("notices:board")), "Choir practice")

    def test_teacher_can_take_down_a_notice(self):
        notice = self.make_notice("Lost property")
        self.client.force_login(self.teacher)
        response = self.client.post(reverse("notices:delete", args=[notice.pk]))
        self.assertRedirects(response, reverse("notices:dashboard"))
        self.assertFalse(Notice.objects.filter(pk=notice.pk).exists())

    def test_form_rejects_expiry_in_the_past(self):
        form = NoticeForm(
            data={"title": "Late", "body": "x", "expires_on": timezone.localdate() - timedelta(days=2)}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("expires_on", form.errors)
