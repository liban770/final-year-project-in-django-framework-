from django import forms

from users.models import User
from .models import Chapter, Feedback, Project, SupervisorAssignment, GroupMember, ContactMessage


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["project_title", "description", "leader"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit leader choices to students only
        self.fields['leader'].queryset = User.objects.filter(role=User.Role.STUDENT)
        self.fields['project_title'].widget.attrs.update({
            'minlength': '5',
            'required': 'required',
        })
        self.fields['description'].widget.attrs.update({
            'minlength': '20',
            'required': 'required',
        })

    def clean_project_title(self):
        title = (self.cleaned_data.get('project_title') or '').strip()
        if len(title) < 5:
            raise forms.ValidationError('Project title must be at least 5 characters long.')

        existing = Project.objects.filter(project_title__iexact=title)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError('This project idea already exists. Please submit a different idea.')

        return title

    def clean_description(self):
        description = (self.cleaned_data.get('description') or '').strip()
        if len(description) < 20:
            raise forms.ValidationError('Project description must be at least 20 characters long.')
        return description


class GroupMemberForm(forms.ModelForm):
    class Meta:
        model = GroupMember
        fields = ["name", "email"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter member name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter member email (optional)'}),
        }


class ContactMessageForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ["name", "email", "message"]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'your.email@example.com'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Your message...', 'rows': 5}),
        }


class ChapterForm(forms.ModelForm):
    class Meta:
        model = Chapter
        fields = ["title", "file"]


class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["comment"]


class SupervisorAssignmentForm(forms.ModelForm):
    class Meta:
        model = SupervisorAssignment
        fields = ["student", "supervisor"]
