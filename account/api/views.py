from django import db
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.mixins import UpdateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from account.models import MailingList, MailingListEmail, Profile
from profiles.api.views import update_postal_code_result
from profiles.models import Result

from .serializers import ProfileSerializer, SubscribeSerializer, UnSubscribeSerializer

all_views = []


class UnsubscribeRateThrottle(AnonRateThrottle):
    """
    The AnonRateThrottle will only ever throttle unauthenticated users.
    The IP address of the incoming request is used to generate a unique key to throttle against.
    """

    rate = "10/day"


class ProfileViewSet(UpdateModelMixin, viewsets.GenericViewSet):
    queryset = Profile.objects.all().select_related("user").order_by("id")
    serializer_class = ProfileSerializer

    def get_permissions(self):
        if self.action in ["unsubscribe"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def update(self, request, *args, **kwargs):
        user = request.user
        instance = user.profile
        serializer = self.serializer_class(
            instance=instance, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            """
            To ensure the postal code results are updated before the user exists the poll.
            After the questions are answered the front-end updates the profile information with a put request.
            """

            if (
                request.method == "PUT"
                and serializer.data.get("postal_code", None) is not None
            ):
                update_postal_code_result(user)
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
        description="Unaubscribe the email from the mailing list attached to the result."
        f"Note, there is a rate-limit of {UnsubscribeRateThrottle.rate} requests.",
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
        throttle_classes=[UnsubscribeRateThrottle],
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


all_views.append({"class": ProfileViewSet, "name": "profile"})
