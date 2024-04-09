import django_filters
from rest_framework.exceptions import ValidationError
from rest_framework.throttling import AnonRateThrottle

from profiles.models import PostalCodeResult


def blur_count(count, threshold=5):
    """
    Returns a blurred count, which is supposed to hide individual
    postal code results.
    """
    if count <= threshold:
        return 0
    else:
        return count


class StartPollRateThrottle(AnonRateThrottle):
    """
    The AnonRateThrottle will only ever throttle unauthenticated users.
    The IP address of the incoming request is used to generate a unique key to throttle against.
    """

    rate = "10/day"


class CustomValidationError(ValidationError):
    # The detail field is shown also when DEBUG=False
    # Ensures the error message is displayed to the user
    def __init__(self, detail):
        super().__init__({"detail": detail})


class PostalCodeResultParamValidator:
    def validate_postal_code(self, param):
        try:
            int(param)
        except:  # noqa E722
            raise CustomValidationError("'postal_code' needs to be int")

    def validate_postal_code_type(self, param):
        try:
            int(param)
        except:  # noqa E722
            raise CustomValidationError("'postal_code_type' needs to be int")


class PostalCodeResultFilter(django_filters.FilterSet, PostalCodeResultParamValidator):
    validate_fields = (
        "postal_code",
        "postal_code_type",
    )
    postal_code = django_filters.NumberFilter()
    postal_code_type = django_filters.NumberFilter()

    postal_code_string = django_filters.CharFilter(method="filter_postal_code_string")
    postal_code_type_string = django_filters.CharFilter(
        method="filter_postal_code_type_string"
    )

    def __init__(self, *args, **kwargs):
        super(PostalCodeResultFilter, self).__init__(*args, **kwargs)
        for query_key, query_value in self.request.query_params.items():
            validator = getattr(self, "validate_%s" % query_key, None)
            if validator:
                validator(query_value)

    def filter_postal_code_string(self, queryset, name, value):
        return queryset.filter(postal_code__postal_code=value)

    def filter_postal_code_type_string(self, queryset, name, value):
        return queryset.filter(postal_code_type__type_name=value)

    class Meta:
        model = PostalCodeResult
        fields = ("postal_code", "postal_code_type")
