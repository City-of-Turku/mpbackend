from django.contrib.auth import get_user, login
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from account.models import User
from profiles.models import (
    Answer,
    Option,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
)
from profiles.utils import get_user_result

from .serializers import (
    AnswerSerializer,
    OptionSerializer,
    QuestionConditionSerializer,
    QuestionSerializer,
    ResultSerializer,
    SubQuestionSerializer,
)

all_views = []


def register_view(klass, name, basename=None):
    entry = {"class": klass, "name": name}
    if basename is not None:
        entry["basename"] = basename
    all_views.append(entry)


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[AllowAny],
    )
    def start_poll(self, request):
        # TODO check recaptha
        user = User.objects.order_by("-id").first()
        if user:
            next_id = user.id + 1
        # Empty User table
        else:
            next_id = 1
        password = User.objects.make_random_password()
        username = f"anonymous_{next_id}"
        user = User.objects.create(
            username=username, password=password, is_generated=True
        )

        login(request, user)
        # assert user.id == next_id
        return Response(status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=["GET"],
        permission_classes=[IsAuthenticated],
    )
    def get_question(self, request):
        number = request.query_params.get("number", None)
        question = Question.objects.get(number=number) # noqa F401       
        breakpoint()

    @action(
        detail=False,
        methods=["GET"],
    )
    def end_poll(self, request):
        pass


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

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        # permission_classes = [AllowAny]
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
                assert answer.user == user
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
        return Response(serializer.data)


register_view(AnswerViewSet, "answer")
