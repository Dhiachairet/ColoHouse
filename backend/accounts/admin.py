from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Campus, RoommateProfile, User


class CustomUserAdmin(UserAdmin):
    ordering = ['email']
    list_display = ['email', 'first_name', 'last_name', 'university', 'campus', 'is_staff']
    search_fields = ['email', 'first_name', 'last_name']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'phone', 'profile_picture', 'bio')}),
        ('Studies', {'fields': ('university', 'field_of_study', 'campus')}),
        ('Notifications', {'fields': ('push_enabled', 'notify_requests', 'notify_messages')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'usable_password', 'password1', 'password2'),
        }),
    )


admin.site.register(User, CustomUserAdmin)
admin.site.register(Campus)
admin.site.register(RoommateProfile)
