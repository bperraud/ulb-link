from django.forms import ModelForm
from link.models import Link
from django import forms


class LinkForm(ModelForm):
    class Meta:
        model = Link
        fields = ["token", "target_url"]
        widgets = {
            "target_url": forms.TextInput(attrs={"style": "width: 100%;"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["target_url"].disabled = True
