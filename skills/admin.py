from django.contrib import admin
from .models import SkillCategory, Skill, Booking, Review


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider', 'category', 'delivery_method', 'min_price', 'max_price', 'is_active']
    list_filter = ['category', 'delivery_method', 'is_active']
    search_fields = ['title', 'provider__email']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['skill', 'client', 'provider', 'session_date', 'agreed_price', 'status']
    list_filter = ['status']
    search_fields = ['skill__title', 'client__email', 'provider__email']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer', 'skill', 'rating', 'created_at']
    list_filter = ['rating']
