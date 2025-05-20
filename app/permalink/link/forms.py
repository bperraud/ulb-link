from django.forms import ModelForm
from link.models import Link
from django import forms


class LinkForm(ModelForm):
    target_url = forms.URLField(label="Share Target URL", required=False, disabled=True)
    expiration = forms.DateField(label="Expiration Date", required=False, disabled=True)

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
