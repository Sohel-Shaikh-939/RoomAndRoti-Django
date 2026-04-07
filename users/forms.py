from django.contrib.auth.forms import UserCreationForm
from django import forms
from .models import CustomUser, StudentProfile


class StudentRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ("email",)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "student"
        if commit:
            user.save()
        return user


class OwnerRegistrationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ("email",)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = "owner"
        if commit:
            user.save()
        return user


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            "target_budget",
            "preferred_food",
            "requires_ac",
            "requires_wifi",
            "requires_bathroom",
        ]
