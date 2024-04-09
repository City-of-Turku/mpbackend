from django.contrib.auth import get_user_model
from rest_framework import serializers

from account.models import MailingListEmail, Profile


class SubscribeSerializer(serializers.Serializer):
    email = serializers.CharField()
    result = serializers.IntegerField()


class UnSubscribeSerializer(serializers.Serializer):
    email = serializers.CharField()


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "last_login",
            "date_joined",
            "is_staff",
            "is_active",
            "email_verified",
        ]


class ProfileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = [
            "id",
            "year_of_birth",
            "postal_code",
            "optional_postal_code",
            "is_filled_for_fun",
            "is_interested_in_mobility",
            "result_can_be_used",
            "gender",
        ]


class MailingListEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = MailingListEmail
        fields = "__all__"
