from rest_framework import serializers

from profiles.models import (
    Result,
    Answer,
    Option,
    OptionGroup,
    Question,
    QuestionCondition,
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


class OptionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionGroup
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
        representation["options"] = OptionSerializer(obj.options, many=True).data
        return representation


class QuestionConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionCondition
        fields = "__all__"


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = "__all__"
