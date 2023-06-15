import uuid

from django.conf import settings
from django.contrib.auth import get_user, login, logout
from django.contrib.auth.hashers import make_password
from django.utils.module_loading import import_string
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from account.api.serializers import PublicUserSerializer
from account.models import Profile, User
from profiles.api.serializers import (
    AnswerSerializer,
    OptionSerializer,
    QuestionConditionSerializer,
    QuestionNumberSerializer,
    QuestionSerializer,
    ResultSerializer,
    SubQuestionSerializer,
)
from profiles.models import (
    Answer,
    Option,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
)
from profiles.utils import generate_password, get_user_result

DEFAULT_RENDERERS = [
    import_string(renderer_module)
    for renderer_module in settings.REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]
]
all_views = []


def register_view(klass, name, basename=None):
    entry = {"class": klass, "name": name}
    if basename is not None:
        entry["basename"] = basename
    all_views.append(entry)


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    renderer_classes = DEFAULT_RENDERERS

    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[AllowAny],
    )
    def start_poll(self, request):
        # TODO check recaptha
        uuid4 = uuid.uuid4()
        username = f"anonymous_{str(uuid4)}"
        user = User.objects.create(pk=uuid4, username=username, is_generated=True)
        password = make_password(generate_password())
        user.password = password
        user.profile = Profile.objects.create(user=user)
        user.save()
        login(request, user)
        serializer = PublicUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_question_numbers(self, request):
        queryset = Question.objects.all().order_by("number")
        page = self.paginate_queryset(queryset)
        serializer = QuestionNumberSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False,
        methods=["GET"],
    )
    def get_question(self, request):
        number = request.query_params.get("number", None)
        if number:
            try:
                question = Question.objects.get(number=number)
            except Question.DoesNotExist:
                return Response(
                    f"question with number {number} not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
            serializer = QuestionSerializer(question)
            return Response(serializer.data, status=status.HTTP_200_OK)

        else:
            return Response(
                "'number' argument not given", status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def end_poll(self, request):
        logout(request)
        return Response("Poll ended, user logged out.", status=status.HTTP_200_OK)


register_view(QuestionViewSet, "question")


class QuestionConditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionCondition.objects.all()
    serializer_class = QuestionConditionSerializer


register_view(QuestionConditionViewSet, "questioncondition")


class OptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer


register_view(OptionViewSet, "option")


class SubQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubQuestion.objects.all()
    serializer_class = SubQuestionSerializer


register_view(SubQuestionViewSet, "subquestion")


class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


register_view(ResultViewSet, "result")


class AnswerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    renderer_classes = DEFAULT_RENDERERS

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def create(self, request, *args, **kwargs):
        option_id = request.data.get("option", None)
        if option_id:
            try:
                option = Option.objects.get(id=option_id)
            except Option.DoesNotExist:
                return Response(
                    f"Option {option_id} not found", status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
                "'option' argument not given", status=status.HTTP_400_BAD_REQUEST
            )

        user = get_user(request)
        if user and option:
            queryset = Answer.objects.filter(user=user, option=option)
            if queryset.count() == 0:
                Answer.objects.create(user=user, option=option)
            else:
                # Update existing answer
                answer = queryset.first()
                answer.option = option
                answer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response("Not created", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
    )
    def get_result(self, request, *args, **kwargs):
        user = get_user(request)
        if not user.is_authenticated:
            return Response(
                "No authentication credentials were provided in the request.",
                status=status.HTTP_403_FORBIDDEN,
            )
        result = get_user_result(user)
        serializer = ResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


register_view(AnswerViewSet, "answer")
