from rest_framework import serializers

from profiles.models import (
    Animal,
    Answer,
    Option,
    OptionGroup,
    Question,
    QuestionCondition,
)


class AnimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Animal
        fields = "__all__"


class OptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Option
        fields = "__all__"

    def to_representation(self, obj):
        representation = super().to_representation(obj)
        representation["animals"] = AnimalSerializer(obj.animals, many=True).data
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
