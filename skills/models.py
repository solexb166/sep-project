from django.db import models
from django.conf import settings
from cloudinary.models import CloudinaryField


class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=50, blank=True)
    image = CloudinaryField('skill_category_image', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Skill Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Skill(models.Model):
    DELIVERY_CHOICES = [
        ('In-Person', 'In-Person'),
        ('Online', 'Online'),
        ('Flexible', 'Flexible'),
    ]

    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='skills'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(SkillCategory, on_delete=models.SET_NULL, null=True, related_name='skills')
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES)
    min_price = models.DecimalField(max_digits=12, decimal_places=0)
    max_price = models.DecimalField(max_digits=12, decimal_places=0)
    is_active = models.BooleanField(default=True)
    is_group_session = models.BooleanField(default=False)
    max_group_size = models.PositiveIntegerField(default=1)
    portfolio_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.provider.get_full_name()}"

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 0
        return round(sum(r.rating for r in reviews) / len(reviews), 1)

    @property
    def review_count(self):
        return self.reviews.count()


class Booking(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Disputed', 'Disputed'),
    ]

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='bookings')
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bookings_as_client'
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='bookings_as_provider'
    )
    session_date = models.DateTimeField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=1, default=1)
    agreed_price = models.DecimalField(max_digits=12, decimal_places=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.client.get_full_name()} -> {self.skill.title} ({self.status})"

    @property
    def has_review(self):
        return hasattr(self, 'review')


class Review(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='review')
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer.get_full_name()} rated {self.skill.title} {self.rating}/5"
