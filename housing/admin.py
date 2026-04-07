from django.contrib import admin
from .models import PG, Room


class RoomInline(admin.TabularInline):
    model = Room
    extra = 1


@admin.register(PG)
class PGAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "starting_price", "gender_restriction")
    list_filter = ("gender_restriction", "has_wifi", "has_ac", "food_included")
    search_fields = ("name", "address")
    inlines = [RoomInline]
