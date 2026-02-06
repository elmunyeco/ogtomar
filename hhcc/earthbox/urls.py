# earthbox/urls.py
from django.urls import path
from . import views

app_name = "earthbox"

urlpatterns = [
    path('', views.home, name='home'),
    path('echo/', views.echo, name='echo'),
]
