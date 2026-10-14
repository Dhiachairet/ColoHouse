from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models


class Campus(models.Model):
    name = models.CharField(max_length=150)
    university = models.CharField(max_length=150)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        verbose_name_plural = 'campuses'
        ordering = ['university', 'name']

    def __str__(self):
        return f"{self.name} ({self.university})"


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The email is required')
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)

    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?[0-9]{8,15}$', 'Enter a valid phone number.')],
    )
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)

    university = models.CharField(max_length=150, blank=True)
    field_of_study = models.CharField(max_length=150, blank=True)
    campus = models.ForeignKey(
        Campus, on_delete=models.SET_NULL, null=True, blank=True, related_name='students'
    )

    push_enabled = models.BooleanField(default=True)
    notify_requests = models.BooleanField(default=True)
    notify_messages = models.BooleanField(default=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    def save(self, *args, **kwargs):
        self.email = self.email.lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class RoomType(models.TextChoices):
    PRIVATE = 'private', 'Private room'
    SHARED = 'shared', 'Shared room'
    STUDIO = 'studio', 'Studio'


class SleepSchedule(models.TextChoices):
    EARLY = 'early', 'Early bird'
    NORMAL = 'normal', 'Normal'
    LATE = 'late', 'Night owl'


class RoommateProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='roommate_profile')

    budget = models.PositiveIntegerField(null=True, blank=True)
    preferred_room_type = models.CharField(max_length=10, choices=RoomType.choices, blank=True)
    move_in_date = models.DateField(null=True, blank=True)
    max_distance_to_campus = models.FloatField(
        null=True, blank=True, validators=[MinValueValidator(0)]
    )

    sleep_schedule = models.CharField(max_length=10, choices=SleepSchedule.choices, blank=True)
    noise_tolerance = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    cleanliness = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    smoker = models.BooleanField(default=False)
    accepts_smokers = models.BooleanField(default=True)

    looking_for_room = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Preferences of {self.user}"
