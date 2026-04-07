from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Notification, StudentProfile


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["email", "username", "role", "is_staff"]
    fieldsets = UserAdmin.fieldsets + ((None, {"fields": ("role",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + ((None, {"fields": ("role",)}),)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Notification)
admin.site.register(StudentProfile)
