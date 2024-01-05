import uuid
import json
import re

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


def user_directory_path(instance, filename):
    return f"user_{instance.user1.id}/{filename}"


class Conversation(models.Model):
    CSV = 'csv'
    DB = 'db'
    SOURCE_CHOICE = (
        (CSV, CSV),
        (DB, DB)
    )
    title = models.CharField(max_length=250)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user1 = models.ForeignKey(User, on_delete=models.CASCADE)
    attachment = models.FileField(null=True, blank=True, upload_to=user_directory_path)
    connection_string = models.TextField(blank=True, null=True)
    data_type = models.CharField(choices=SOURCE_CHOICE, max_length=200)
    timestamp = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)

    def get_title(self):
        return self.attachment.name.split('/',)[-1]

    def get_subtitle(self):
        first_user_msg = self.message_set.filter(user__isnull=False).first()
        content = first_user_msg.extract_json()
        if content == "NA":
            return first_user_msg.content
        return first_user_msg.extract_json()['answer'][:50]


class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False, blank=False)

    # class Meta:
    #     ordering = ['-timestamp']

    def __str__(self):
        return self.content[:50]

    def extract_json(self):
        try:
            return json.loads(self.content)
        except json.JSONDecodeError:

            # Regular expression pattern to extract JSON
            # This pattern assumes the JSON object starts with '{' and ends with '}'
            # Adjust as needed (e.g., if JSON arrays '[]' are possible)
            json_pattern = r'{.*}'
            match = re.search(json_pattern, self.content, re.DOTALL)

            if match:
                # Extract the JSON string
                json_str = match.group()
                # Parse the JSON string
                json_data = json.loads(json_str)
                return json_data
            else:
                return "NA"

        except Exception as e:
            return f"Error: {e}"

    @property
    def images(self):
        try:
            return self.extract_json()['graphs']
        except TypeError:
            return []
