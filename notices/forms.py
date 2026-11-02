from django import forms
from django.utils import timezone

from reports.models import SchoolClass

from .models import Notice


class NoticeForm(forms.ModelForm):
    audience = forms.ModelMultipleChoiceField(
        queryset=SchoolClass.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Leave all unticked to post to the whole school.",
    )

    class Meta:
        model = Notice
        fields = ["title", "body", "audience", "pinned", "expires_on"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 6}),
            "expires_on": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
        }

    def clean_expires_on(self):
        expires_on = self.cleaned_data.get("expires_on")
        if expires_on and expires_on < timezone.localdate():
            raise forms.ValidationError("The expiry date can't be in the past.")
        return expires_on
