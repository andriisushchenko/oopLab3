from django.urls import path
from . import views

urlpatterns = [
    path('players/', views.create_player),
    path('players/login/', views.login_player),
    path('players/<int:player_id>/', views.get_player),
    path('matches/', views.list_matches),
    path('matches/create/', views.create_match),
    path('matches/<int:match_id>/finish/', views.finish_match),
    path('users/<int:player_id>/top-up/', views.top_up_balance),
    path('users/<int:player_id>/withdraw/', views.withdraw_money),
    path('bets/place/', views.place_bet),
]