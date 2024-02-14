from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError


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


class PostalCodeResultFilter(filters.FilterSet, PostalCodeResultParamValidator):
    validate_fields = (
        "postal_code",
        "postal_code_type",
    )

    def __init__(self, *args, **kwargs):
        super(PostalCodeResultFilter, self).__init__(*args, **kwargs)
        for query_key, query_value in self.request.query_params.items():
            validator = getattr(self, "validate_%s" % query_key, None)
            if validator:
                validator(query_value)
