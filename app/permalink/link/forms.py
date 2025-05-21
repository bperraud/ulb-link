from django.forms import ModelForm
from link.models import Link
from django import forms

from datetime import date, timedelta

class LinkForm(ModelForm):
    target_url = forms.URLField(label="Share Target URL", required=False, disabled=True)
    # expiration = forms.DateField(label="Expiration Date", required=False, disabled=True)
    expiration = forms.DateField(
        label="Expiration Date",
        required=False,
        widget=forms.DateInput(
            attrs={"type": "date",
                    "min": date.today().strftime("%Y-%m-%d"),
                    "max": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"),  # max date = 1 year from today
                  }
        )
    )

    class Meta:
        model = Link
        fields = ["token"]
        widgets = {
            "target_url": forms.TextInput(attrs={"style": "width: 100%;"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.share:
            self.fields["target_url"].initial = self.instance.share.target_url
            self.fields["expiration"].initial = self.instance.share.expiration

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Update share.expiration
        expiration = self.cleaned_data.get("expiration")
        if instance.share and expiration:
            instance.share.expiration = expiration
            instance.share.save()
        if commit:
            instance.save()
        return instance
