from rest_framework import serializers

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


class ResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Result
        fields = "__all__"


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = "__all__"

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation["results"] = ResultSerializer(obj.results, many=True).data
        return representation


class SubQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubQuestion
        fields = "__all__"

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation["options"] = OptionSerializer(obj.options, many=True).data
        return representation


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = "__all__"

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        if hasattr(obj, "options") and obj.options.count() > 0:
            representation["options"] = OptionSerializer(obj.options, many=True).data
        elif hasattr(obj, "sub_questions") and obj.sub_questions.count() > 0:
            representation["sub_questions"] = SubQuestionSerializer(
                obj.sub_questions, many=True
            ).data

        return representation


class QuestionRequestSerializer(serializers.Serializer):
    question = serializers.IntegerField()


class AnswerRequestSerializer(QuestionRequestSerializer):
    option = serializers.IntegerField()
    sub_question = serializers.IntegerField()


class ConditionMetRequestSerializer(AnswerRequestSerializer):
    pass


class InConditionResponseSerializer(serializers.Serializer):
    in_condition = serializers.BooleanField()


class QuestionNumberIDSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ["id", "number"]


class QuestionConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCondition
        fields = "__all__"


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"


class PostalCodeResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostalCodeResult
        fields = "__all__"


class PostalCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostalCode
        fields = "__all__"
