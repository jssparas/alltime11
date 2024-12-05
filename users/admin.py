from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone_number", "username", "email", "name", "is_staff")
    list_filter = ("is_staff", "is_active")
    search_fields = ("username", "name", "phone_number")
    ordering = ("pk",)
