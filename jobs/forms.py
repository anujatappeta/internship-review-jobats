from django import forms
from .models import Candidate, JobApplication

class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ['full_name', 'email', 'phone', 'portfolio_url', 'skills']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Jane Doe', 'id': 'id_full_name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'jane.doe@example.com', 'id': 'id_email'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890', 'id': 'id_phone'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://janedoe.dev', 'id': 'id_portfolio_url'}),
            'skills': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Python, React, SQL', 'id': 'id_skills'}),
        }

    def validate_unique(self):
        exclude = self._get_validation_exclusions()
        exclude.add('email')
        try:
            self.instance.validate_unique(exclude=exclude)
        except forms.ValidationError as e:
            self._update_errors(e)


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = ['cover_letter']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Tell us why you are a great fit...', 'id': 'id_cover_letter'}),
        }
