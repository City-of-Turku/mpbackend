import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    result = models.ForeignKey(
        "profiles.Result",
        related_name="users",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    email = models.EmailField(unique=True, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_generated = models.BooleanField(default=False)
    # Flag that is used to ensure the user is only Once calculated to the PostalCodeResults model.
    postal_code_result_saved = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """Makes email lowercase always"""
        if self.email:
            self.email = self.email.lower() if len(self.email) > 0 else self.email
        super(User, self).save(*args, **kwargs)

    class Meta:
        db_table = "auth_user"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True)
    optional_postal_code = models.CharField(max_length=10, null=True)
    is_filled_for_fun = models.BooleanField(default=False)
    result_can_be_used = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username
