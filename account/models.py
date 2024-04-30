import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from profiles.models import Result


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
    has_subscribed = models.BooleanField(default=False)
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
    GENDER_OPTIONS = [
        ("M", "Male"),
        ("F", "Female"),
        ("X", "X"),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    year_of_birth = models.PositiveSmallIntegerField(null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True)
    optional_postal_code = models.CharField(max_length=10, null=True)
    is_interested_in_mobility = models.BooleanField(default=False)
    result_can_be_used = models.BooleanField(default=True)
    gender = models.CharField(
        max_length=2, choices=GENDER_OPTIONS, null=True, blank=True
    )

    def __str__(self):
        return self.user.username


class MailingList(models.Model):
    result = models.ForeignKey(
        Result,
        related_name="mailing_list",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def __str__(self):
        return getattr(self.result, "topic", None)

    @property
    def csv_emails(self):
        return ",".join([e.email for e in self.emails.all()])

    def number_of_emails(self):
        return self.emails.count()


class MailingListEmail(models.Model):
    email = models.EmailField()
    mailing_list = models.ForeignKey(
        MailingList, related_name="emails", on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.email} {self.mailing_list}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email", "mailing_list"],
                name="email_and_mailing_list_must_be_jointly:unique",
            )
        ]
