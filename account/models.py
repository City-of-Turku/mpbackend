from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    result = models.ForeignKey(
        "profiles.Result",
        related_name="users",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_generated = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Makes email lowercase always"""
        self.email = self.email.lower()
        super(User, self).save(*args, **kwargs)

    class Meta:
        db_table = "auth_user"


class Profile(models.Model):
    GENDER_OPTIONS = [
        ("M", "Male"),
        ("F", "Female"),
        ("NB", "Nonbinary"),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    gender = models.CharField(max_length=2, choices=GENDER_OPTIONS, blank=True)

    def __str__(self):
        return self.user.username
