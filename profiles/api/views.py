import logging
import uuid

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError, transaction
from django.utils.module_loading import import_string
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiResponse,
)
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.mixins import CreateModelMixin
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from account.api.serializers import PublicUserSerializer
from account.models import Profile, User
from profiles.api.serializers import (
    AnswerRequestSerializer,
    AnswerSerializer,
    InConditionResponseSerializer,
    OptionSerializer,
    PostalCodeResultSerializer,
    PostalCodeSerializer,
    PostalCodeTypeSerializer,
    QuestionConditionSerializer,
    QuestionNumberIDSerializer,
    QuestionRequestSerializer,
    QuestionSerializer,
    ResultSerializer,
    SubQuestionConditionSerializer,
    SubQuestionRequestSerializer,
    SubQuestionSerializer,
)
from profiles.models import (
    Answer,
    Option,
    PostalCode,
    PostalCodeResult,
    PostalCodeType,
    Question,
    QuestionCondition,
    Result,
    SubQuestion,
    SubQuestionCondition,
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


def sub_question_condition_met(sub_question_condition, user):
    if (
        Answer.objects.filter(user=user, option=sub_question_condition.option).count()
        > 0
    ):
        return True
    return False


def question_condition_met(question_condition_qs, user):
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
            return True
    return False


@transaction.atomic
def update_postal_code_result(user):
    # Ensure that duplicate results are not saved, profiles filled for fun are ignored and
    # profiles whos result can not be used are ignored.

    if (
        user.postal_code_result_saved
        or user.profile.is_filled_for_fun
        or not user.profile.result_can_be_used
    ):
        return
    if user.result:
        result = user.result
    else:
        result = get_user_result(user)
    if not result:
        return
    postal_code = None
    postal_code_type = None
    if user.profile.postal_code:
        postal_code, _ = PostalCode.objects.get_or_create(
            postal_code=user.profile.postal_code
        )
        postal_code_type, _ = PostalCodeType.objects.get_or_create(
            type_name=PostalCodeType.HOME_POSTAL_CODE
        )
    if user.profile.optional_postal_code:
        postal_code, _ = PostalCode.objects.get_or_create(
            postal_code=user.profile.optional_postal_code
        )
        postal_code_type, _ = PostalCodeType.objects.get_or_create(
            type_name=PostalCodeType.OPTIONAL_POSTAL_CODE
        )

    try:
        postal_code_result, _ = PostalCodeResult.objects.get_or_create(
            postal_code=postal_code, postal_code_type=postal_code_type, result=result
        )
    except IntegrityError as e:
        logger.error(f"IntegrityError while creating PostalCodeResult: {e}")
        return
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
        token, _ = Token.objects.get_or_create(user=user)
        response_data = {"token": token.key, "id": user.id}
        return Response(response_data, status=status.HTTP_200_OK)

    @extend_schema(
        description="Return the numbers of questions",
        parameters=[],
        examples=None,
        responses={200: QuestionNumberIDSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["GET"],
    )
    def get_question_numbers(self, request):
        queryset = Question.objects.all().order_by("id")
        page = self.paginate_queryset(queryset)
        serializer = QuestionNumberIDSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @extend_schema(
        description="Returns the questions that have a condition.",
        parameters=[],
        examples=None,
        responses={200: QuestionSerializer(many=True)},
    )
    @action(
        detail=False,
        methods=["GET"],
    )
    def get_questions_with_conditions(self, request):
        queryset = Question.objects.filter(question_conditions__isnull=False)
        page = self.paginate_queryset(queryset)
        serializer = QuestionSerializer(page, many=True)
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
        description="Ends the poll for the user by logging out the user. Updates also the PostalCodeResult table."
        "Must be called after poll is finnished.",
        parameters=[],
        examples=None,
        responses={200: None},
        request=None,
    )
    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def end_poll(self, request):
        user = request.user
        update_postal_code_result(user)
        user.auth_token.delete()
        return Response("Poll ended.", status=status.HTTP_200_OK)

    @extend_schema(
        description="Checks if condition met. Returns 'true' if the user has answered the given conditions "
        "of the question in such a way that the given question should be asked. "
        "The information of the if the condition is met, should be fetched before Every question, except the first",
        request=QuestionRequestSerializer,
        responses={
            200: OpenApiResponse(description="true or false"),
            400: OpenApiResponse(description="'question' argument not given"),
            404: OpenApiResponse(
                description="'Question' or 'QuestionCondition' row not found"
            ),
        },
    )
    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def check_if_question_condition_met(self, request):
        user = request.user
        question_id = request.data.get("question", None)
        if not question_id:
            return Response(
                "'question_id' argument not given",
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
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
        if question_condition_met(question_condition_qs, user):
            return Response({"condition_met": True}, status=status.HTTP_200_OK)

        return Response({"condition_met": False}, status=status.HTTP_200_OK)

    @extend_schema(
        description="Checks if condition met for a sub question."
        "Returns 'true', if the condition is met or there is no condition."
        "Returns 'false', if the user has answered previous questions in way,"
        " that the sub question should not be questioned/displayed for the user.",
        request=SubQuestionRequestSerializer,
        responses={
            200: OpenApiResponse(description="true or false"),
            400: OpenApiResponse(description="'sub_question' argument not given"),
            404: OpenApiResponse(
                description="'SubQuestion' or 'SubQuestionCondition' row not found"
            ),
        },
    )
    @action(detail=False, methods=["POST"], permission_classes=[IsAuthenticated])
    def check_if_sub_question_condition_met(self, request):
        user = request.user
        sub_question_id = request.data.get("sub_question", None)
        if not sub_question_id:
            return Response(
                "'sub_question_id' argument not given",
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                sub_question = SubQuestion.objects.get(id=sub_question_id)
            except SubQuestion.DoesNotExist:
                return Response(
                    f"Question {sub_question_id} not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
        sub_question_condition = SubQuestionCondition.objects.filter(
            sub_question=sub_question
        ).first()
        # Condition is met if no condition is found
        condition_met = True
        if sub_question_condition:
            if not sub_question_condition_met(sub_question_condition, user):
                condition_met = False

        return Response({"condition_met": condition_met}, status=status.HTTP_200_OK)

    @extend_schema(
        description="Check if question is in condition. If the question is not in a condition"
        ", it is not required to post the answers of the question immediately after they are given.",
        examples=None,
        request=QuestionRequestSerializer,
        responses={
            200: InConditionResponseSerializer,
            404: OpenApiResponse(description="'Question' not found"),
        },
    )
    @action(
        detail=False,
        methods=["POST"],
        permission_classes=[IsAuthenticated],
    )
    def in_condition(self, request, *args, **kwargs):
        question_id = request.data.get("question", None)
        response_data = {"in_condition": False}

        if not question_id:
            return Response(
                "'question_id' argument not given",
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                question = Question.objects.get(id=question_id)
            except Question.DoesNotExist:
                return Response(
                    f"Question {question_id} not found",
                    status=status.HTTP_404_NOT_FOUND,
                )

        qs = QuestionCondition.objects.filter(question_condition=question)
        if qs.count() > 0:
            response_data["in_condition"] = True
        serializer = InConditionResponseSerializer(data=response_data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


register_view(QuestionViewSet, "question")


class QuestionConditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionCondition.objects.all()
    serializer_class = QuestionConditionSerializer


register_view(QuestionConditionViewSet, "questioncondition")


class SubQuestionConditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubQuestionCondition.objects.all()
    serializer_class = SubQuestionConditionSerializer


register_view(SubQuestionConditionViewSet, "subquestioncondition")


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


class AnswerViewSet(CreateModelMixin, GenericViewSet):
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
        description="Create an answer for the user that is logged in."
        "Note, if same user, question and optionally sub question is given the answer will be"
        " updated with the new option.",
        request=AnswerRequestSerializer,
        responses={
            201: OpenApiResponse(description="created"),
            400: OpenApiResponse(
                description="'option' or 'question' argument not given"
            ),
            404: OpenApiResponse(
                description="'option', 'question' or 'sub_question'  not found"
            ),
            405: OpenApiResponse(
                description="Question or sub question condition not met,"
                " i.e. the user has answered so that this question cannot be answered"
            ),
            500: OpenApiResponse(description="Not created"),
        },
    )
    def create(self, request, *args, **kwargs):
        user = request.user
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
            question = Question.objects.get(id=question_id)
        except Question.DoesNotExist:
            return Response(
                f"Question {question_id} not found", status=status.HTTP_404_NOT_FOUND
            )
        if question.num_sub_questions > 0:
            try:
                sub_question = SubQuestion.objects.get(
                    id=sub_question_id, question=question
                )
            except SubQuestion.DoesNotExist:
                return Response(
                    f"SubQuestion {sub_question_id} not found or wrong related question.",
                    status=status.HTTP_404_NOT_FOUND,
                )

        if sub_question:
            try:
                option = Option.objects.get(id=option_id, sub_question=sub_question)
            except Option.DoesNotExist:
                return Response(
                    f"Option {option_id} not found or wrong related or sub_question.",
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            try:
                option = Option.objects.get(id=option_id, question=question)
            except Option.DoesNotExist:
                return Response(
                    f"Option {option_id} not found or wrong related question.",
                    status=status.HTTP_404_NOT_FOUND,
                )

        question_condition_qs = QuestionCondition.objects.filter(question=question)
        if question_condition_qs.count() > 0:
            if not question_condition_met(question_condition_qs, user):
                return Response(
                    "Question condition not met, i.e. the user has answered so that this question cannot be answered",
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
                )
        sub_question_condition = SubQuestionCondition.objects.filter(
            sub_question=sub_question
        ).first()
        if sub_question_condition:
            if not sub_question_condition_met(sub_question_condition, user):
                return Response(
                    "SubQuestion condition not met, "
                    "i.e. the user has answered so that this sub question cannot be answered",
                    status=status.HTTP_405_METHOD_NOT_ALLOWED,
                )
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
        user = request.user
        if not user.is_authenticated:
            return Response(
                "No authentication credentials were provided in the request.",
                status=status.HTTP_403_FORBIDDEN,
            )
        result = get_user_result(user)
        serializer = ResultSerializer(result)
        return Response(serializer.data, status=status.HTTP_200_OK)


register_view(AnswerViewSet, "answer")

POSTAL_CODE_PARAM = OpenApiParameter(
    name="postal_code",
    location=OpenApiParameter.QUERY,
    description="'id' of the PostalCode instance. Empty value is treated as null and results for "
    "user answers that have not provided a postal code will be returned",
    required=False,
    type=int,
)
POSTAL_CODE_TYPE_PARAM = OpenApiParameter(
    name="postal_code_type",
    location=OpenApiParameter.QUERY,
    description="'id' of the PostalCodeType instance. Empty value is treated as null",
    required=False,
    type=int,
)


@extend_schema_view(
    list=extend_schema(
        parameters=[POSTAL_CODE_PARAM, POSTAL_CODE_TYPE_PARAM],
        description="Returns aggregated results per postal code and/or postal code type.",
    )
)
class PostalCodeResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PostalCodeResult.objects.all()
    serializer_class = PostalCodeResultSerializer

    def list(self, request, *args, **kwargs):
        queryset = None
        qs1 = None
        qs2 = None
        postal_code_id = request.query_params.get("postal_code", None)
        postal_code_type_id = request.query_params.get("postal_code_type", None)
        if postal_code_id:
            try:
                postal_code = PostalCode.objects.get(id=postal_code_id)
            except PostalCode.DoesNotExist:
                return Response(
                    f"PostalCode {postal_code_id} not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Postal code is not mandatory
            postal_code = None

        if postal_code_type_id:
            try:
                postal_code_type = PostalCodeType.objects.get(id=postal_code_type_id)
            except PostalCodeType.DoesNotExist:
                return Response(
                    f"PostalCodeType {postal_code_type_id} not found",
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            # Postal code type is not mandatory
            postal_code_type = None

        # Make possible to query with None value in query params
        # as all users do not provide a postal code
        if "postal_code" in request.query_params:
            qs1 = PostalCodeResult.objects.filter(postal_code=postal_code)
        if "postal_code_type" in request.query_params:
            qs2 = PostalCodeResult.objects.filter(postal_code_type=postal_code_type)

        if qs1 and qs2:
            queryset = qs1.intersection(qs2)
        elif qs1 or qs2:
            queryset = qs1 if qs1 else qs2
        else:
            queryset = self.queryset

        page = self.paginate_queryset(queryset)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


register_view(PostalCodeResultViewSet, "postalcoderesult")


class PostalCodeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PostalCode.objects.all()
    serializer_class = PostalCodeSerializer


register_view(PostalCodeViewSet, "postalcode")


class PostalCodeTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = PostalCodeType.objects.all()
    serializer_class = PostalCodeTypeSerializer


register_view(PostalCodeViewSet, "postalcodetype")
