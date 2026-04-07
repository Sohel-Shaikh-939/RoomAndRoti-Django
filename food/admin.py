from django.contrib import admin
from .models import Mess, DailyMenu


class DailyMenuInline(admin.StackedInline):
    model = DailyMenu
    extra = 1


@admin.register(Mess)
class MessAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "monthly_fee", "is_veg_only", "has_non_veg")
    list_filter = ("is_veg_only", "has_jain_food", "has_non_veg")
    search_fields = ("name", "address")
    inlines = [DailyMenuInline]


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ("mess", "date")
    list_filter = ("date", "mess")
