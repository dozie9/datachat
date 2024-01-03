from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.Home.as_view(), name='home'),
    path('data-upload/', views.DataUploadView.as_view(), name='data-upload'),
    path('convo/<conversation_id>/', views.FileChatView.as_view(), name='file-chat'),
]
