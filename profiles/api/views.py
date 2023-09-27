import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user, login, logout
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.utils.module_loading import import_string
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from account.api.serializers import PublicUserSerializer
from account.models import Profile, User
from profiles.api.serializers import (
    AnswerRequestSerializer,
    AnswerSerializer,
    ConditionMetRequestSerializer,
    HasConditionResponseSerializer,
    OptionSerializer,
    PostalCodeResultSerializer,
    QuestionConditionSerializer,
    QuestionNumberIDSerializer,
    QuestionRequestSerializer,
    QuestionSerializer,
    ResultSerializer,
    SubQuestionSerializer,
)
from profiles.models import (
    Answer,
    Option,
    PostalCode,
    PostalCodeResult,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
)
from profiles.utils import generate_password, get_user_result

logger = logging.getLogger(__name__)

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


def get_or_create_row(model, filter):
    results = model.objects.filter(**filter)
    if results.exists():
        return results.first(), False
    else:
        return model.objects.create(**filter), True


@transaction.atomic
def update_result_counts(user):
    # Ensure that duplicate results are not saved
    if user.postal_code_result_saved:
        return
    if user.result:
        result = user.result
    else:
        result = get_user_result(user)
    postal_code = None
    postal_code_type = None
    if user.profile.postal_code:
        postal_code, _ = PostalCode.objects.get_or_create(
            postal_code=user.profile.postal_code
        )
        postal_code_type = PostalCodeResult.HOME_POSTAL_CODE
    if user.profile.optional_postal_code:
        postal_code, _ = PostalCode.objects.get_or_create(
            postal_code=user.profile.optional_postal_code
        )
        postal_code_type = PostalCodeResult.OPTIONAL_POSTAL_CODE

    try:
        postal_code_result, _ = PostalCodeResult.objects.get_or_create(
            postal_code=postal_code, postal_code_type=postal_code_type, result=result
        )
    except IntegrityError as e:
        logger.error(f"IntegrityError while creating PostalCodeResult: {e}")
    postal_code_result.count += 1
    postal_code_result.save()
    user.postal_code_result_saved = True
    user.save()


class QuestionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    renderer_classes = DEFAULT_RENDERERS

    @extend_schema(
        description="Start the Poll for a anonymous user. Creates a anonymous user and logs the user in."
        " Returns the id of the user.",
        parameters=[],
        examples=None,
        request=None,
        responses={200: PublicUserSerializer},
    )
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

    @extend_schema(
        description="Return the numbers of questions",
        parameters=[],
        examples=None,
        responses={200: QuestionNumberIDSerializer},
    )
    @action(
        detail=False,
        methods=["GET"],
    )
    def get_question_numbers(self, request):
        queryset = Question.objects.all().order_by("number")
        page = self.paginate_queryset(queryset)
        serializer = QuestionNumberIDSerializer(page, many=True)
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

    @extend_schema(
        description="Ends the poll for the user by logging out the user.",
        parameters=[],
        examples=None,
        responses={200: None},
        request=None,
    )
    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def end_poll(self, request):
        user = get_user(request)
        update_result_counts(user)
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

    @extend_schema(
        description="Create an answer for the user that is logged in by posting the id of option.",
        request=AnswerRequestSerializer,
        responses={
            201: {
                "description": "created",
            },
            400: {"description": "'option' or 'question' argument not given"},
            404: {
                "description": "'option', 'question' or 'sub_question'  not found",
            },
            500: {"description": "Not created, user not logged in."},
        },
    )
    def create(self, request, *args, **kwargs):
        option_id = request.data.get("option", None)
        question_id = request.data.get("question", None)
        sub_question_id = request.data.get("sub_question", None)
        sub_question = None
        if not option_id:
            return Response(
                "'option' argument not given", status=status.HTTP_400_BAD_REQUEST
            )

        if not question_id:
            return Response(
                "'question' argument not given", status=status.HTTP_400_BAD_REQUEST
            )

        try:
            option = Option.objects.get(id=option_id)
        except Option.DoesNotExist:
            return Response(
                f"Option {option_id} not found", status=status.HTTP_404_NOT_FOUND
            )

        try:
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                f"Question {question_id} not found", status=status.HTTP_404_NOT_FOUND
            )
        if question.num_sub_questions > 0:
            try:
                sub_question = SubQuestion.objects.get(id=sub_question_id)
            except SubQuestion.DoesNotExist:
                return Response(
                    f"SubQuestion {sub_question_id} not found",
                    status=status.HTTP_404_NOT_FOUND,
                )

        user = get_user(request)
        if user:
            filter = {"user": user, "question": question, "sub_question": sub_question}
            queryset = Answer.objects.filter(**filter)
            if queryset.count() == 0:
                filter["option"] = option
                Answer.objects.create(**filter)
            else:
                # Update existing answer
                answer = queryset.first()
                answer.option = option
                answer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response("Not created", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @extend_schema(
        description="Checks if condition met. Returns 'true' if the user has answered the given conditions "
        "of the question in such a way that the given question should be asked.",
        request=ConditionMetRequestSerializer,
        responses={
            200: {
                "description": "true false",
            },
            400: {"description": "'question' argument not given"},
            404: {
                "description": "'Question' or 'QuestionCondition' not found",
            },
        },
    )
    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def check_if_condition_met(self, request):
        user = get_user(request)
        question_id = request.data.get("question", None)
        if not question_id:
            return Response(
                "'question_id' argument not given",
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                question = Question.objects.get(id=question_id)
            except Option.DoesNotExist:
                return Response(
                    f"Question {question_id} not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
        # Retrive the conditions for the question, note can have multiple conditions
        question_condition_qs = QuestionCondition.objects.filter(question=question)
        if question_condition_qs.count() == 0:
            return Response(
                f"QuestionCondition not found for question number {question_id}",
                status=status.HTTP_404_NOT_FOUND,
            )
        for question_condition in question_condition_qs:
            if question_condition.sub_question_condition:
                user_answers = Answer.objects.filter(
                    user=user,
                    option__sub_question=question_condition.sub_question_condition,
                ).values_list("option", flat="True")
            else:
                user_answers = Answer.objects.filter(
                    user=user, option__question=question_condition.question_condition
                ).values_list("option", flat="True")

            option_conditions = question_condition.option_conditions.all().values_list(
                "id", flat=True
            )
            if set(user_answers).intersection(set(option_conditions)):
                return Response({"condition_met": True}, status=status.HTTP_200_OK)

        return Response({"condition_met": False}, status=status.HTTP_200_OK)

    @extend_schema(
        description="Return the current result(animal) of the authenticated user",
        examples=None,
        responses={200: ResultSerializer},
    )
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

    @extend_schema(
        description="Check if question has condition. If the question does not have a condition"
        ", it is not required to post the answer immediately after the answer is given.",
        examples=None,
        request=QuestionRequestSerializer,
        responses={
            200: HasConditionResponseSerializer,
            404: {
                "description": "'Question' not found",
            },
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
    )
    def has_condition(self, request, *args, **kwargs):
        question_id = request.data.get("question", None)
        response_data = {"has_condition": False}

        if not question_id:
            return Response(
                "'question_id' argument not given",
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                question = Question.objects.get(id=question_id)
            except Option.DoesNotExist:
                return Response(
                    f"Question {question_id} not found",
                    status=status.HTTP_404_NOT_FOUND,
                )

        qs = QuestionCondition.objects.filter(question_condition=question)
        if qs.count() > 0:
            response_data["has_condition"] = True
        serializer = HasConditionResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


register_view(AnswerViewSet, "answer")


class PostalCodeResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PostalCodeResult.objects.all()
    serializer_class = PostalCodeResultSerializer


register_view(PostalCodeResultViewSet, "postalcoderesult")
