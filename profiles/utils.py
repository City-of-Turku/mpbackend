from profiles.models import Answer, Result


def get_user_result(user):
    answer_qs = Answer.objects.filter(user=user)
    if answer_qs.count() == 0:
        return None

    results = {r: 0 for r in Result.objects.all()}
    for answer in answer_qs:
        for result in answer.option.results.all():
            results[result] += 1
    result = max(results, key=results.get)
    return result
