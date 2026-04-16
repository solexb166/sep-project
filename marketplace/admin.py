from django.contrib import admin
from .models import Category, Listing, ListingImage, Wishlist, Message


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon']
    prepopulated_fields = {'slug': ('name',)}


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    max_num = 5


def unflag_listings(modeladmin, request, queryset):
    queryset.update(is_flagged=False)
unflag_listings.short_description = "Unflag selected listings"


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'category', 'price', 'condition', 'is_flagged', 'is_sold', 'is_active', 'created_at']
    list_filter = ['category', 'condition', 'is_flagged', 'is_sold', 'is_active']
    search_fields = ['title', 'seller__email', 'seller__first_name']
    actions = [unflag_listings]
    inlines = [ListingImageInline]
    readonly_fields = ['views_count', 'created_at', 'updated_at']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['sender', 'receiver', 'listing', 'is_read', 'created_at']
    list_filter = ['is_read']
    search_fields = ['sender__email', 'receiver__email']
