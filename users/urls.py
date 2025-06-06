from django.urls import path
from . import views

urlpatterns = [
    path('enter/', views.enter_event_code, name='enter_event_code'),
    path('join/<str:event_code>/', views.enter_username, name='enter_username'),
    path('waiting/<str:event_code>/', views.waiting_room, name='waiting_room'),
    path('event/state/<str:event_code>/', views.event_state, name='event_state'),
    path('host/dashboard/', views.host_dashboard, name='host_dashboard'),
    path('host/start/<str:event_code>/', views.start_event, name='start_event'),
    path('leaderboard/<str:event_code>/', views.leaderboard, name='live_leaderboard'),
    path('leaderboard/state/<int:event_id>/', views.leaderboard_state, name='leaderboard_state'),

]
