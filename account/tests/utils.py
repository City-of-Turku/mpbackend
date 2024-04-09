def patch(api_client, url, data=None, status_code=200):
    response = api_client.patch(url, data)
    assert response.status_code == status_code, "%s %s" % (
        response.status_code,
        response.data,
    )
    return response.json()


def check_method_status_codes(api_client, urls, methods, status_code, **kwargs):
    # accept also a single url as a string
    if isinstance(urls, str):
        urls = (urls,)

    for url in urls:
        for method in methods:
            response = getattr(api_client, method)(url)
            assert (
                response.status_code == status_code
            ), "%s %s expected %s, got %s %s" % (
                method,
                url,
                status_code,
                response.status_code,
                response.data,
            )
            error_code = kwargs.get("error_code")
            if error_code:
                assert (
                    response.data["code"] == error_code
                ), "%s %s expected error_code %s, got %s" % (
                    method,
                    url,
                    error_code,
                    response.data["code"],
                )
