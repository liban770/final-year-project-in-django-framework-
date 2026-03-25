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
