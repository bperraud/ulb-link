from django.forms import ModelForm
from link.models import Link
from django import forms

from datetime import date, timedelta
    

input_style = "bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-primary-600 focus:border-primary-600 block w-full p-2.5 dark:bg-gray-600 dark:border-gray-500 dark:placeholder-gray-400 dark:text-white dark:focus:ring-primary-500 dark:focus:border-primary-500"

label_style = "block mb-2 text-sm font-medium text-gray-900 dark:text-white"

class LinkForm(ModelForm):

    target_url = forms.URLField(
        label="Share Target URL",
        required=False,
        disabled=True,
        widget=forms.URLInput(
            attrs={
                "class": input_style
            }
        ),
    )

    expiration = forms.DateField(
        label="Expiration Date",
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "min": date.today().strftime("%Y-%m-%d"),
                "max": (date.today() + timedelta(days=365)).strftime("%Y-%m-%d"),
            }
        ),
    )

    class Meta:
        model = Link
        fields = ["token"]
        widgets = {
            "token": forms.TextInput(attrs={"class": input_style}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.share:
            self.fields["target_url"].initial = self.instance.share.target_url
            self.fields["expiration"].initial = self.instance.share.expiration
        else:
            self.fields.pop("expiration", None)
            self.fields["target_url"].disabled = False
            self.fields["target_url"].initial = self.instance.direct_target_url


    def save(self, commit=True):
        instance = super().save(commit=False)
        # Update share.expiration
        expiration = self.cleaned_data.get("expiration")
        if instance.share and expiration:
            instance.share.expiration = expiration
            instance.share.save()
        else :
            instance.direct_target_url = self.cleaned_data.get("target_url")
        if commit:
            instance.save()
        return instance

