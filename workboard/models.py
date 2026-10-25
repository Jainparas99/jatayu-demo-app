from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Card(models.Model):
    """Human-readable work item codes are imported from a team's existing tracker."""

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACTIVE = "active", "In progress"
        DONE = "done", "Done"

    code = models.CharField(primary_key=True, max_length=40)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    estimate = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["code"]
        index_together = [("owner", "status")]

    def __str__(self):
        return f"{self.code}: {self.title}"
