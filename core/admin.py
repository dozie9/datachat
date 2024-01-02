from django.contrib import admin

from core.models import Conversation, Message


@admin.register(Conversation)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user1', 'data_type']


@admin.register(Message)
class UserAdmin(admin.ModelAdmin):
    list_display = ['user', 'conversation', 'timestamp']

