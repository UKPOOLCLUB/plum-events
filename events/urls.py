from django.urls import path
from . import views

urlpatterns = [
    path('golf/score-entry/<int:group_id>/', views.enter_golf_scores, name='enter_golf_scores'),
    path('golf/my-score-entry/<str:event_code>/', views.redirect_to_golf_group, name='my_golf_score_entry'),
    path('golf/save-score/', views.save_golf_score, name='save_golf_score'),


]
