from django.conf import settings

from core.models import Conversation


def get_conversations(_request):
    if not _request.user.is_authenticated:
        return
    return {'CONVERSATIONS': Conversation.objects.filter(user1=_request.user)}
