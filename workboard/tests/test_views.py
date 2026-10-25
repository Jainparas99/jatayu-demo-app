from datetime import date
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import translation

from workboard.models import Card
from workboard.services import due_at_utc


class BoardTests(TestCase):
    def setUp(self):
        self.alice = get_user_model().objects.create_user("alice")
        self.bob = get_user_model().objects.create_user("bob")
        self.own = Card.objects.create(
            code="OPS-001", owner=self.alice, title="Upgrade runner", estimate=Decimal("1234.50")
        )
        self.other = Card.objects.create(code="PRIVATE-001", owner=self.bob, title="Private task")
        self.client.force_login(self.alice)

    def payload(self, **changes):
        return {
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "1",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-code": self.own.code,
            "form-0-title": self.own.title,
            "form-0-status": "open",
            "form-0-estimate": "1234.50",
            **changes,
        }

    def test_anonymous_board_requires_login(self):
        response = Client().get(reverse("board"))
        self.assertRedirects(response, "/accounts/login/?next=/", fetch_redirect_response=False)

    def test_anonymous_bulk_edit_requires_login(self):
        response = Client().post(reverse("edit-cards"), self.payload())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Card.objects.filter(pk=self.own.pk).exists())

    def test_board_shows_own_work_only(self):
        response = self.client.get(reverse("board"))
        self.assertContains(response, "Upgrade runner")
        self.assertNotContains(response, "Private task")

    def test_empty_queue_has_helpful_message(self):
        Card.objects.filter(owner=self.alice).delete()
        self.assertContains(self.client.get(reverse("board")), "Your queue is clear")

    def test_single_card_heading(self):
        self.assertContains(self.client.get(reverse("board")), "1 work item")

    def test_status_filter_is_used_by_board(self):
        self.own.status = "done"
        self.own.save()
        self.assertContains(
            self.client.get(reverse("board"), {"status": "open"}), "Your queue is clear"
        )

    @override_settings(LANGUAGE_CODE="de", USE_L10N=False)
    def test_budget_stays_machine_readable_in_translated_interface(self):
        with translation.override("de"):
            self.assertContains(self.client.get(reverse("board")), ">1234.50<", html=False)

    def test_bulk_editor_never_lists_another_users_card(self):
        response = self.client.get(reverse("edit-cards"))
        self.assertContains(response, "OPS-001")
        self.assertNotContains(response, "PRIVATE-001")

    def test_bulk_edit_updates_owned_card(self):
        response = self.client.post(
            reverse("edit-cards"), self.payload(**{"form-0-title": "Updated"})
        )
        self.assertRedirects(response, reverse("board"), fetch_redirect_response=False)
        self.own.refresh_from_db()
        self.assertEqual(self.own.title, "Updated")
        self.other.refresh_from_db()
        self.assertEqual(self.other.title, "Private task")

    def test_bulk_delete_deletes_owned_card(self):
        response = self.client.post(reverse("edit-cards"), self.payload(**{"form-0-DELETE": "on"}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Card.objects.filter(pk=self.own.pk).exists())
        self.assertTrue(Card.objects.filter(pk=self.other.pk).exists())

    def test_invalid_bulk_edit_leaves_database_unchanged(self):
        response = self.client.post(
            reverse("edit-cards"), self.payload(**{"form-0-estimate": "-1"})
        )
        self.assertEqual(response.status_code, 400)
        self.own.refresh_from_db()
        self.assertEqual(self.own.estimate, Decimal("1234.50"))

    def test_csrf_is_required_for_browser_bulk_edit(self):
        browser = Client(enforce_csrf_checks=True)
        browser.force_login(self.alice)
        self.assertEqual(browser.post(reverse("edit-cards"), self.payload()).status_code, 403)

    def test_schedule_updates_only_open_owned_cards(self):
        done = Card.objects.create(
            code="OPS-DONE", owner=self.alice, title="Finished", status="done"
        )
        response = self.client.post(reverse("schedule-cards"), {"day": "2026-11-03"})
        self.assertEqual(response.status_code, 302)
        self.own.refresh_from_db()
        self.assertEqual(self.own.due_at, due_at_utc(date(2026, 11, 3)))
        done.refresh_from_db()
        self.other.refresh_from_db()
        self.assertIsNone(done.due_at)
        self.assertIsNone(self.other.due_at)

    def test_invalid_schedule_returns_validation_error(self):
        response = self.client.post(reverse("schedule-cards"), {"day": "bad-date"})
        self.assertContains(response, "Choose a valid date", status_code=400)

    def test_schedule_requires_post(self):
        self.assertEqual(self.client.get(reverse("schedule-cards")).status_code, 405)

    def test_export_download_excludes_other_owners(self):
        with (
            TemporaryDirectory() as folder,
            override_settings(
                EXPORT_ROOT=folder,
                DEFAULT_FILE_STORAGE="workboard.storage.ExportStorage",
            ),
        ):
            response = self.client.get(reverse("export-cards"))
            self.assertEqual(response.status_code, 200)
            content = b"".join(response.streaming_content).decode()
            response.close()
            self.assertIn("OPS-001,Upgrade runner,open,1234.50", content)
            self.assertNotIn("PRIVATE-001", content)
