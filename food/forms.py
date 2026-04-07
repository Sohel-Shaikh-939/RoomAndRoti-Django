from django import forms
from .models import Mess


class MessForm(forms.ModelForm):
    class Meta:
        model = Mess
        fields = [
            "name",
            "address",
            "contact_number",
            "monthly_fee",
            "single_meal_fee",
            "is_veg_only",
            "has_jain_food",
            "has_non_veg",
            "image",
            "latitude",
            "longitude",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }
