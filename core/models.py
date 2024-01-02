from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


def user_directory_path(instance, filename):
    return f"user_{instance.user.id}/{filename}"


class Conversation(models.Model):
    CSV = 'csv'
    DB = 'db'
    SOURCE_CHOICE = (
        (CSV, CSV),
        (DB, DB)
    )
    title = models.CharField(max_length=250)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE)
    attachment = models.FileField(null=True, blank=True, upload_to=user_directory_path)
    connection_string = models.TextField(blank=True, null=True)
    data_type = models.CharField(choices=SOURCE_CHOICE, max_length=200)


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)

    def __str__(self):
        return self.content[:50]
