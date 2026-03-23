from django import forms

from .models import Chapter, Feedback, Project, SupervisorAssignment


class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["title", "description"]


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
