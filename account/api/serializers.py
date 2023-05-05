from django.contrib.auth import get_user_model
from rest_framework import serializers

from account.models import Profile


class PublicUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["id"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
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
    """Profile serializer that also shows info from User model"""

    user_info = UserSerializer(
        many=False, read_only=True, source="user", required=False
    )

    class Meta:
        model = Profile
        fields = ["user_info"]
