import pytest
from rest_framework.reverse import reverse


@pytest.mark.django_db
def test_list_postal_code(api_client, postal_codes):
    response = api_client.get(reverse("profiles:postalcode-list"))
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["count"] == postal_codes.count()
    assert json_data["results"][0]["id"] == postal_codes.first().id
    assert json_data["results"][0]["postal_code"] == postal_codes.first().postal_code
