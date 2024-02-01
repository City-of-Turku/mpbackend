import pytest
from django.db.utils import IntegrityError

from profiles.models import PostalCode, PostalCodeResult, PostalCodeType, Result


@pytest.mark.django_db
def test_postal_code_result_create_no_exception_raised(results):
    postal_code = None
    postal_code_type = None
    result = Result.objects.first()
    # Raises no exception both postal_code and postal_code_type is null
    try:
        PostalCodeResult.objects.create(
            result=result,
            postal_code=postal_code,
            postal_code_type=postal_code_type,
        )
    except IntegrityError:
        assert False

    postal_code = PostalCode.objects.create(postal_code="20210")
    postal_code_type = PostalCodeType.objects.create(type_name="work")
    # Raises no exception both postal_code and postal_code_type is null
    try:
        PostalCodeResult.objects.create(
            result=result,
            postal_code=postal_code,
            postal_code_type=postal_code_type,
        )
    except IntegrityError:
        assert False


@pytest.mark.django_db
def test_postal_code_reslut_create_exception_raised(results):
    result = Result.objects.first()
    postal_code_type = None
    # As both postal_code an postal_code_type must be jointly null, raises exception
    postal_code = PostalCode.objects.create(postal_code="20210")
    with pytest.raises(IntegrityError) as excinfo:
        PostalCodeResult.objects.create(
            result=result,
            postal_code=postal_code,
            postal_code_type=postal_code_type,
        )
    assert PostalCodeResult._meta.constraints[0].name in str(excinfo)
