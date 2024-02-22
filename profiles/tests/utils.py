from memoize import delete_memoized

from profiles.utils import get_num_results_per_option


def delete_memoized_functions_cache(func):
    def wrapper():
        delete_memoized(get_num_results_per_option)

    return wrapper
