from django.conf import settings
from django.db.models import Max

from core.models import Conversation


def get_conversations(_request):
    if not _request.user.is_authenticated:
        return []
    conversation_qs = Conversation.objects.filter(user1=_request.user).alias(
        latest_message=Max('message__timestamp')
    ).order_by('-latest_message')

    return {'CONVERSATIONS': conversation_qs}
