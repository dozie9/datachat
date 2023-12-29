from django.urls import path
from . import views

urlpatterns = [
    path('', views.TemplateView.as_view(), name='home'),
]
