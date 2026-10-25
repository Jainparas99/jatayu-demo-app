import csv
import io
from datetime import datetime

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.utils import timezone

from .models import Card


def due_at_utc(day):
    """The ops team measures its end-of-day deadline at 17:00 UTC."""
    return datetime(day.year, day.month, day.day, 17, tzinfo=timezone.utc)


def cards_for(user, status=None):
    cards = Card.objects.filter(owner=user)
    if status in Card.Status.values:
        cards = cards.filter(status=status)
    return cards


def export_cards(user):
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["code", "title", "status", "estimate"])
    for card in cards_for(user):
        # Prevent spreadsheet software interpreting user content as formulas.
        title = "'" + card.title if card.title.startswith(("=", "+", "-", "@")) else card.title
        writer.writerow([card.code, title, card.status, str(card.estimate)])
    return default_storage.save(f"queue-{user.pk}.csv", ContentFile(output.getvalue().encode()))
