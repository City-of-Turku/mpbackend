import datetime

from django.conf import settings
from django.contrib.auth import get_user_model
# from django.contrib.auth import authenticate, login
# from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from account.models import Profile

from .serializers import ProfileSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all().select_related("user").order_by("id")

    serializer_class = ProfileSerializer

    def get_permissions(self):
        if self.action in ["register", "login", "email_verify_confirm"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
    )
    def email_verify_request(self, request, *args, **kwargs):
        email = request.query_params.get("email", None)
        user = request.user
        if not email:
            return Response(
                "No email supplied in request parameters.",
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            user.email = email
            user.save()
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
        except (TypeError, ValueError, ValidationError, user_model.DoesNotExist):
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

    # @action(
    #     detail=False,
    #     methods=["POST"],
    #     permission_classes=[AllowAny],
    # )
    # def register(self, request, *args, **kwargs):
    #     password1 = request.data.get("password1")
    #     password2 = request.data.get("password2")
    #     # TODO Uncomment when front end is ready
    #     # try:
    #     #     password1 = base64.b64decode(request.data.get("password1")).decode()
    #     #     password2 = base64.b64decode(request.data.get("password2")).decode()
    #     # except:
    #     #     return Response("Password parameters are not base64 encoded or not present.",
    #     #  status=status.HTTP_400_BAD_REQUEST)
    #     if password1 != password2:
    #         return Response(
    #             "Passwords don't match.", status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # try:
    #     #     validate_password(password1)
    #     # except ValidationError as err:
    #     # return Response({"password1": err}, status=status.HTTP_400_BAD_REQUEST)

    #     # TODO Add Recaptcha

    #     user_serializer = UserSerializer(data=request.data)
    #     user_serializer.is_valid(raise_exception=True)
    #     user = user_serializer.save()
    #     user.set_password(password1)
    #     user.is_active = True
    #     user.save()
    #     return Response("User created.", status=status.HTTP_201_CREATED)

    # @action(
    #     detail=False,
    #     methods=["POST"],
    #     permission_classes=[AllowAny],
    # )
    # def login(self, request, *args, **kwargs):
    #     password = request.data.get("password", None)
    #     username = request.data.get("username", None)
    #     user = authenticate(request, username=username, password=password)
    #     if user is not None:
    #         if user.is_active:
    #             login(request, user)
    #             return HttpResponse("Authentication successfull")
    #         else:
    #             return HttpResponse("Disabled account")
    #     else:
    #         return HttpResponse("User not found")
