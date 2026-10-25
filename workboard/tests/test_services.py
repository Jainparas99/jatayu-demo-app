from datetime import UTC, date
from pathlib import Path
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.test import TestCase, override_settings

from workboard.models import Card
from workboard.services import due_at_utc, export_cards


class ServiceTests(TestCase):
    def test_deadline_uses_utc_and_ops_cutoff(self):
        deadline = due_at_utc(date(2026, 11, 3))
        self.assertEqual(deadline.hour, 17)
        self.assertEqual(deadline.tzinfo, UTC)

    def test_exports_use_dedicated_storage_not_general_uploads(self):
        user = get_user_model().objects.create_user("reporter")
        Card.objects.create(code="REP-001", owner=user, title="Report")
        with (
            TemporaryDirectory() as folder,
            override_settings(
                EXPORT_ROOT=folder,
                MEDIA_ROOT=str(Path(folder) / "uploads"),
                DEFAULT_FILE_STORAGE="workboard.storage.ExportStorage",
            ),
        ):
            name = export_cards(user)
            self.assertEqual(Path(default_storage.path(name)).parent, Path(folder))
            self.assertEqual(default_storage.url(name), f"/exports/{name}")
            self.assertIn("REP-001", Path(default_storage.path(name)).read_text())

    def test_csv_title_is_escaped_for_spreadsheet_import(self):
        user = get_user_model().objects.create_user("reporter")
        Card.objects.create(code="REP-001", owner=user, title="=1+1")
        with (
            TemporaryDirectory() as folder,
            override_settings(
                EXPORT_ROOT=folder,
                DEFAULT_FILE_STORAGE="workboard.storage.ExportStorage",
            ),
        ):
            name = export_cards(user)
            with default_storage.open(name, "rb") as export:
                self.assertIn("'=1+1", export.read().decode())
