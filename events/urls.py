from django.urls import path
from . import views

urlpatterns = [
    path('golf/score-entry/<int:group_id>/', views.enter_golf_scores, name='enter_golf_scores'),
    path('golf/my-score-entry/<str:event_code>/', views.redirect_to_golf_group, name='my_golf_score_entry'),
    path('golf/save-score/', views.save_golf_score, name='save_golf_score'),
    path('golf/submit-scorecard/<int:group_id>/', views.submit_golf_scorecard, name='submit_golf_scorecard'),
    path('golf/state/<int:group_id>/', views.golf_scorecard_state, name='golf_scorecard_state'),
    path('table-tennis/<int:event_id>/', views.table_tennis_game_view, name='table_tennis_game_view'),
    path('table-tennis/<int:event_id>/submit/<int:winner_id>/', views.submit_table_tennis_result, name='submit_table_tennis_result'),
    path('tabletennis/state/<int:event_id>/', views.table_tennis_state, name='table_tennis_state'),
    path('pool/league/<int:event_id>/', views.pool_league_view, name='pool_league_view'),
    path('pool-league/submit-result/', views.submit_pool_match_result, name='submit_pool_match_result'),
    path('pool_league/state/<int:event_id>/', views.pool_league_state, name='pool_league_state'),
    path('event/<int:event_id>/e-darts/', views.enter_edarts_results, name='enter_edarts_results'),
    path('events/edarts/submit/<int:event_id>/<int:group_id>/', views.submit_edarts_group, name='submit_darts_group'),
    path('killer/<int:event_id>/', views.killer_game_view, name='killer_game'),
    path('killer/<int:event_id>/submit/', views.killer_submit_turn, name='killer_submit_turn'),
    path('killer/state/<int:event_id>/', views.killer_game_state, name='killer_game_state'),

]
