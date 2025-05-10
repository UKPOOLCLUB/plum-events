from django.urls import path
from . import views

urlpatterns = [
    path('enter/', views.enter_event_code, name='enter_event_code'),
]
