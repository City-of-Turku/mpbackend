from django.db.models.signals import post_save
from django.dispatch import receiver

from profiles.models import Answer
from profiles.utils import get_user_result


@receiver(post_save, sender=Answer)
def answer_on_save(sender, **kwargs):
    obj = kwargs["instance"]
    user = obj.user
    user.result = get_user_result(user)
    user.save()
