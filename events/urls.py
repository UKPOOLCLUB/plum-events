from django.urls import path
from . import views

urlpatterns = [
    path('golf/score-entry/<int:group_id>/', views.enter_golf_scores, name='enter_golf_scores'),
    path('golf/my-score-entry/<str:event_code>/', views.redirect_to_golf_group, name='my_golf_score_entry'),
    path('golf/save-score/', views.save_golf_score, name='save_golf_score'),
    path('golf/submit-scorecard/<int:group_id>/', views.submit_golf_scorecard, name='submit_golf_scorecard'),
    path('table-tennis/<int:event_id>/', views.table_tennis_game_view, name='table_tennis_game_view'),
    path('table-tennis/<int:event_id>/submit/<int:winner_id>/', views.submit_table_tennis_result, name='submit_table_tennis_result'),
    path('event/<int:event_id>/pool-league/matrix/', views.pool_league_matrix_view, name='pool_league_matrix'),
    path('pool-league/submit-result/', views.submit_pool_match_result, name='submit_pool_match_result'),

]
