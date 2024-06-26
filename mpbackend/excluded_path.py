# https://stackoverflow.com/questions/68943065/django-drf-spectacular-can-you-exclude-specific-paths

DOC_ENDPOINTS = [
    "/api/v1/question/",
    "/api/v1/answer/",
    "/api/v1/postalcoderesult/",
    "/api/v1/cumulativeresult/",
    "/api/account/",
]


def preprocessing_filter_spec(endpoints):
    filtered = []
    for endpoint in DOC_ENDPOINTS:
        for path, path_regex, method, callback in endpoints:
            if path.startswith(endpoint):
                filtered.append((path, path_regex, method, callback))
    return filtered
