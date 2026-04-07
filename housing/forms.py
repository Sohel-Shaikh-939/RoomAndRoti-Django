from django import forms
from .models import PG, Room


class PGForm(forms.ModelForm):
    class Meta:
        model = PG
        fields = [
            "name",
            "address",
            "contact_number",
            "gender_restriction",
            "food_included",
            "has_wifi",
            "has_ac",
            "attached_bathroom",
            "starting_price",
            "image",
            "latitude",
            "longitude",
        ]
        widgets = {
            "address": forms.Textarea(attrs={"rows": 3}),
        }


class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ["occupancy", "rent_per_month", "vacant_beds"]
        widgets = {
            "occupancy": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
                }
            ),
            "rent_per_month": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
                }
            ),
            "vacant_beds": forms.NumberInput(
                attrs={
                    "class": "mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm px-4 py-2 border"
                }
            ),
        }
