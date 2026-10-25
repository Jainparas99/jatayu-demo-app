from django import forms
from django.forms import modelformset_factory

from .models import Card


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ("code", "title", "status", "estimate")

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("A work item needs a title.")
        return title


# The editable natural primary key is part of the actual bulk-edit form.
# The view limits rows to the authenticated owner; this is the CVE probe's boundary.
CardFormSet = modelformset_factory(Card, form=CardForm, extra=0, can_delete=True)
