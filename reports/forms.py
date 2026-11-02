from django import forms

from .models import EXAM_MAX


class ScoreRowForm(forms.Form):
    student_id = forms.IntegerField(widget=forms.HiddenInput)
    ca = forms.IntegerField(label="CA", min_value=0, max_value=EXAM_MAX, required=False)
    exam = forms.IntegerField(label="Exam", min_value=0, max_value=EXAM_MAX, required=False)

    def clean(self):
        cleaned = super().clean()
        ca, exam = cleaned.get("ca"), cleaned.get("exam")
        if (ca is None) != (exam is None):
            raise forms.ValidationError("Enter both CA and exam, or leave both empty.")
        return cleaned


ScoreFormSet = forms.formset_factory(ScoreRowForm, extra=0)

