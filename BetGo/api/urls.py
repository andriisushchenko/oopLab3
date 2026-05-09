from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_page),
    path('players/', views.create_player),
    path('matches/', views.create_match),
    path('users/<int:player_id>/top-up/', views.top_up_balance),
    path('bets/place/', views.place_bet),
]