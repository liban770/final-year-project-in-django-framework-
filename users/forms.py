from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import User


class AppUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "password1", "password2")


class AppUserUpdateForm(forms.ModelForm):
    """
    Admin-only user edit form (no password editing).
    """

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "role", "is_active", "is_staff")
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500"}
            ),
            "first_name": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500"}
            ),
            "last_name": forms.TextInput(
                attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500"}
            ),
            "role": forms.Select(
                attrs={"class": "w-full rounded-lg border border-slate-300 px-3 py-2 focus:ring-2 focus:ring-indigo-500"}
            ),
        }

    def clean_username(self):
        username = (self.cleaned_data.get("username") or "").strip()
        if not username:
            raise forms.ValidationError("Username is required.")
        return username

    def clean_email(self):
        # Allow blank emails, but normalize if provided.
        email = (self.cleaned_data.get("email") or "").strip()
        return email
