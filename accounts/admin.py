from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, University


def approve_verification(modeladmin, request, queryset):
    queryset.update(is_verified=True)
approve_verification.short_description = "Approve Verification"


def reject_verification(modeladmin, request, queryset):
    queryset.update(is_verified=False, student_id_photo=None, selfie_photo=None)
reject_verification.short_description = "Reject Verification"


def grant_pro(modeladmin, request, queryset):
    from django.utils import timezone
    from datetime import timedelta
    queryset.update(is_pro=True, pro_expires_at=timezone.now() + timedelta(days=30))
grant_pro.short_description = "Grant Pro (30 days)"


def revoke_pro(modeladmin, request, queryset):
    queryset.update(is_pro=False, pro_expires_at=None)
revoke_pro.short_description = "Revoke Pro"


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'get_full_name', 'university', 'is_verified', 'is_pro', 'date_joined')
    list_filter = ('university', 'is_verified', 'is_pro', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    actions = [approve_verification, reject_verification, grant_pro, revoke_pro]
    fieldsets = UserAdmin.fieldsets + (
        ('SEP Profile', {
            'fields': ('phone_number', 'university', 'student_id_number',
                       'student_id_photo', 'selfie_photo', 'profile_picture',
                       'bio', 'date_of_birth', 'is_verified', 'is_pro', 'pro_expires_at')
        }),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'email_domain', 'is_active')
    search_fields = ('name', 'short_name')
    list_filter = ('is_active',)
