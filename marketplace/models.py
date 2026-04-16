from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from cloudinary.models import CloudinaryField


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)
    image = CloudinaryField('category_image', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


def listing_expires_at():
    return timezone.now() + timedelta(days=30)


class Listing(models.Model):
    CONDITION_CHOICES = [
        ('New', 'New'),
        ('Like New', 'Like New'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Poor', 'Poor'),
    ]
    ACQUISITION_CHOICES = [
        ('Bought New', 'Bought New'),
        ('Received as Gift', 'Received as Gift'),
        ('Second-hand Purchase', 'Second-hand Purchase'),
        ('Other', 'Other'),
    ]

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='listings'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=0)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='listings')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    acquisition_source = models.CharField(max_length=50, choices=ACQUISITION_CHOICES)
    serial_number = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    is_sold = models.BooleanField(default=False)
    is_flagged = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(default=listing_expires_at)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def get_primary_image(self):
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary
        return self.images.first()

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at


class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = CloudinaryField('listing_image')
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image for {self.listing.title}"


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='wishlist_items'
    )
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='wishlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.listing.title}"


class Message(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    receiver = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='received_messages'
    )
    listing = models.ForeignKey(
        Listing, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='messages'
    )
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.email} -> {self.receiver.email}: {self.content[:50]}"
