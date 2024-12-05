"""users URL Configuration
"""
from django.urls import path
from .views import UserView

urlpatterns = [
    path('', UserView.as_view()),
    path('<str:uid>', UserView.as_view()),
]
