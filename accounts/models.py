from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from cloudinary.models import CloudinaryField


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required')
        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('first_name', extra_fields.get('first_name', 'Admin'))
        extra_fields.setdefault('last_name', extra_fields.get('last_name', 'User'))
        return self.create_user(email, password, **extra_fields)


class University(models.Model):
    name = models.CharField(max_length=200)
    short_name = models.CharField(max_length=20)
    email_domain = models.CharField(max_length=100)
    logo = CloudinaryField('logo', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Universities'
        ordering = ['name']

    def __str__(self):
        return self.name


class CustomUser(AbstractUser):
    username = models.CharField(max_length=150, unique=True, blank=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, blank=True)
    university = models.ForeignKey(
        University, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='students'
    )
    student_id_number = models.CharField(max_length=50, blank=True)
    student_id_photo = CloudinaryField('student_id', blank=True, null=True)
    selfie_photo = CloudinaryField('selfie', blank=True, null=True)
    profile_picture = CloudinaryField('profile_picture', blank=True, null=True)
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    is_pro = models.BooleanField(default=False)
    pro_expires_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def save(self, *args, **kwargs):
        if not self.username:
            base = self.email.split('@')[0]
            username = base
            count = 1
            while CustomUser.objects.filter(username=username).exclude(pk=self.pk).exists():
                username = f"{base}{count}"
                count += 1
            self.username = username
        super().save(*args, **kwargs)

    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return None

    @property
    def active_listings_count(self):
        return self.listings.filter(is_active=True, is_sold=False).count()

    @property
    def active_skills_count(self):
        return self.skills.filter(is_active=True).count()

    @property
    def daily_messages_count(self):
        from django.utils import timezone
        today = timezone.now().date()
        return self.sent_messages.filter(created_at__date=today).count()

    @property
    def can_create_listing(self):
        if self.is_pro:
            return True
        return self.active_listings_count < 3

    @property
    def can_create_skill(self):
        if self.is_pro:
            return True
        return self.active_skills_count < 2

    @property
    def can_send_message(self):
        if self.is_pro:
            return True
        return self.daily_messages_count < 15
