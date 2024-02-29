import pytest
from rest_framework.reverse import reverse


@pytest.mark.django_db
def test_list_postal_code(api_client, postal_code_types):
    response = api_client.get(reverse("profiles:postalcodetype-list"))
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["count"] == postal_code_types.count()
    assert json_data["results"][0]["id"] == postal_code_types.first().id
    assert json_data["results"][0]["type_name"] == postal_code_types.first().type_name
