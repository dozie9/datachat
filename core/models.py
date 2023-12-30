from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


def user_directory_path(instance, filename):
    return f"user_{instance.user.id}/{filename}"


class Conversation(models.Model):
    tittle = models.CharField(max_length=250)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE)


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)
    attachment = models.FileField(null=True, blank=True, upload_to=user_directory_path)

    def __str__(self):
        return self.content[:50]
