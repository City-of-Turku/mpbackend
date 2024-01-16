import datetime

from django import db
from django.conf import settings
from django.contrib.auth import get_user, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from account.models import MailingList, MailingListEmail, Profile, User
from profiles.models import Result

from .serializers import ProfileSerializer, SubscribeSerializer, UnSubscribeSerializer

all_views = []


class ProfileViewSet(UpdateModelMixin, viewsets.GenericViewSet):

    queryset = Profile.objects.all().select_related("user").order_by("id")

    serializer_class = ProfileSerializer

    def get_permissions(self):
        if self.action in ["unsubscribe", "email_verify_confirm"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        user = get_user(request)
        instance = user.profile
        serializer = self.serializer_class(
            instance=instance, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Subscribe the email to the mailing list attached to the result.",
        request=SubscribeSerializer,
        responses={
            201: OpenApiResponse(description="subscribed"),
            400: OpenApiResponse(
                description="Validation error, detailed information in response"
            ),
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
    )
    @db.transaction.atomic
    def subscribe(self, request):
        result = Result.objects.filter(id=request.data.get("result", None)).first()
        if not result:
            return Response("'result' not found", status=status.HTTP_400_BAD_REQUEST)

        email = request.data.get("email", None)
        if not email:
            return Response("No 'email' provided", status=status.HTTP_400_BAD_REQUEST)
        if MailingListEmail.objects.filter(email=email).count() > 0:
            return Response("'email' exists", status=status.HTTP_400_BAD_REQUEST)
        try:
            validate_email(email)
        except ValidationError as e:
            return Response(f"Invalid email: {e}", status=status.HTTP_400_BAD_REQUEST)
        mailing_list = MailingList.objects.filter(result=result).first()
        if not mailing_list:
            # In case mailing list is not created for the result, it is created.
            mailing_list = MailingList.objects.create(result=result)

        MailingListEmail.objects.create(mailing_list=mailing_list, email=email)
        return Response("subscribed", status=status.HTTP_201_CREATED)

    @extend_schema(
        description="Unaubscribe the email from the mailing list attached to the result.",
        request=UnSubscribeSerializer,
        responses={
            200: OpenApiResponse(description="unsubscribed"),
            400: OpenApiResponse(
                description="Validation error, detailed information in response"
            ),
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[AllowAny],
    )
    def unsubscribe(self, request):
        email = request.data.get("email", None)
        if not email:
            return Response("No 'email' provided", status=status.HTTP_400_BAD_REQUEST)
        qs = MailingListEmail.objects.filter(email=email)
        if not qs.exists():
            return Response(
                f"{email} does not exists", status=status.HTTP_400_BAD_REQUEST
            )

        qs.delete()
        return Response(f"unsubscribed {email}", status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
    )
    def save_email(self, request):
        """
        Endpoint to store users email.

        """
        user = get_user(request)
        email = request.data.get("email", None)
        if not email:
            return Response(
                "No 'email' provided in body.", status=status.HTTP_400_BAD_REQUEST
            )
        if User.objects.filter(email=email).count() > 0:
            return Response(
                f"Email {email} already exists", status=status.HTTP_409_CONFLICT
            )
        user.email = email
        user.save()
        return Response("Email saved", status=status.HTTP_201_CREATED)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
    )
    def email_verify_request(self, request, *args, **kwargs):
        """
        Endpoint to send email verfication email.
        """
        email = request.query_params.get("email", None)
        if not email:
            return Response(
                "No email supplied in request parameters.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = get_user(request)
        if not user:
            return Response("User not found.", status=status.HTTP_404_NOT_FOUND)

        # Send email with uid and token
        uid = user.id
        token = default_token_generator.make_token(user)
        subject = "Verify your email address"
        message = f"{uid} {token}"
        mail_sent = send_mail(subject, message, settings.EMAIL_HOST_USER, [email])
        if mail_sent:
            return Response("Email sent.", status=status.HTTP_200_OK)
        else:
            return Response("Email not sent.", status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[AllowAny],
    )
    def email_verify_confirm(self, request, *args, **kwargs):
        uid = request.data.get("uid", None)
        token = request.data.get("token", None)
        user_model = get_user_model()
        try:
            user = user_model.objects.get(pk=uid)
        except (
            TypeError,
            ValueError,
            OverflowError,
            ValidationError,
            user_model.DoesNotExist,
        ):
            return Response(
                "Email verification unsuccessful.", status=status.HTTP_400_BAD_REQUEST
            )
        if default_token_generator.check_token(user, token):
            user.email_verified = True
            # Invalidate used token by modifying user's last_login
            user.last_login = timezone.now() + datetime.timedelta(seconds=1)
            user.save()
            return Response("Email verified successfully.", status=status.HTTP_200_OK)
        return Response(
            "Email verification unsuccessful.", status=status.HTTP_400_BAD_REQUEST
        )

    class Meta:
        model = Profile
        fields = ["id"]
        lookup_field = "id"


all_views.append({"class": ProfileViewSet, "name": "profile"})
