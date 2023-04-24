from rest_framework import viewsets

from profiles.models import (
    Result,
    Answer,
    Option,
    OptionGroup,
    Question,
    QuestionCondition,
)

from .serializers import (
    ResultSerializer,
    AnswerSerializer,
    OptionGroupSerializer,
    OptionSerializer,
    QuestionConditionSerializer,
    QuestionSerializer,
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


register_view(QuestionViewSet, "question")


class QuestionConditionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = QuestionCondition.objects.all()
    serializer_class = QuestionConditionSerializer


register_view(QuestionConditionViewSet, "questioncondition")


class OptionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Option.objects.all()
    serializer_class = OptionSerializer


register_view(OptionViewSet, "option")


class OptionGroupViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OptionGroup.objects.all()
    serializer_class = OptionGroupSerializer


register_view(OptionGroupViewSet, "optiongroup")


class ResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Result.objects.all()
    serializer_class = ResultSerializer


register_view(ResultViewSet, "result")


class AnswerViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer


register_view(AnswerViewSet, "answer")
