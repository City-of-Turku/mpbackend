import secrets
import string

from account.models import User
from profiles.models import Answer, Result


def get_user_result(user: User) -> Result:
    answer_qs = Answer.objects.filter(user=user)
    if answer_qs.count() == 0:
        return None

    # calculate the cumulative values of options for every result
    cum_results = {r: 0 for r in Result.objects.all()}
    for answer in answer_qs:
        for result in answer.option.results.all():
            cum_results[result] += 1

    # If all cumulative values are 0, return None
    if all(value == 0 for value in cum_results.values()):
        return None
    # calculate the relative result for every result (animal)
    results = {}

    for result in Result.objects.all():
        results[result] = cum_results[result] / result.num_options

    # The result is the highest relative result
    result = max(results, key=results.get)
    return result


def generate_password() -> str:
    """
    https://docs.python.org/3/library/secrets.html#recipes-and-best-practices
    Generate a 10 alphanumeric password with at least one lowercase character,
      at least one uppercase character, and at least three digits:
    """
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet) for i in range(10))
        if (
            any(c.islower() for c in password)
            and any(c.isupper() for c in password)
            and sum(c.isdigit() for c in password) >= 3
        ):
            break
    return password
