from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from workboard.forms import CardFormSet
from workboard.models import Card
from workboard.services import cards_for


class CardTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = get_user_model().objects.create_user("alice")
        cls.bob = get_user_model().objects.create_user("bob")
        Card.objects.create(code="OPS-002", owner=cls.alice, title="Renew certificate")
        Card.objects.create(code="OPS-001", owner=cls.alice, title="Rotate runner", status="active")
        Card.objects.create(code="PRIVATE-001", owner=cls.bob, title="Private task")

    def test_queue_orders_cards_and_limits_owner(self):
        self.assertQuerysetEqual(
            cards_for(self.alice), ["OPS-001", "OPS-002"], transform=lambda card: card.code
        )

    def test_status_filter_returns_only_matching_work(self):
        self.assertQuerysetEqual(
            cards_for(self.alice, "active"), ["OPS-001"], transform=lambda card: card.code
        )

    def test_unknown_filter_does_not_hide_work(self):
        self.assertEqual(cards_for(self.alice, "invalid").count(), 2)

    def test_display_name_contains_tracking_code(self):
        self.assertEqual(str(Card.objects.get(pk="OPS-002")), "OPS-002: Renew certificate")

    def test_negative_budget_is_invalid(self):
        card = Card(code="NEW", owner=self.alice, title="Budget", estimate=Decimal("-1.00"))
        with self.assertRaises(ValidationError):
            card.full_clean()

    def test_natural_primary_key_is_editable_in_real_formset(self):
        formset = CardFormSet(queryset=cards_for(self.alice))
        self.assertIn("code", formset.forms[0].fields)
        self.assertFalse(Card._meta.pk.auto_created)
        self.assertTrue(Card._meta.pk.editable)
