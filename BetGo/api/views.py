from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal
from .models import Player, Match, Bet, Transaction
from django.shortcuts import render

@api_view(['POST'])
def create_player(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if Player.objects.filter(username=username).exists():
        return Response({'error': 'Користувач з таким ім\'ям вже існує'}, status=status.HTTP_400_BAD_REQUEST)

    player = Player.objects.create(
        username=username,
        password=password,
        balance=0
    )
    return Response({'message': 'Гравця створено', 'playerId': player.id}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def create_match(request):
    match = Match.objects.create(
        team1_name=request.data.get('team1Name'),
        team2_name=request.data.get('team2Name'),
        odds_team1=request.data.get('oddsTeam1'),
        odds_team2=request.data.get('oddsTeam2'),
        odds_draw=request.data.get('oddsDraw')
    )
    return Response({'message': 'Матч створено', 'matchId': match.id}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def top_up_balance(request, player_id):
    amount = request.data.get('amount')

    if not amount or Decimal(amount) <= 0:
        return Response({'error': 'Сума поповнення має бути більшою за нуль'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        player = Player.objects.get(id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Користувача не знайдено'}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        player.balance += Decimal(amount)
        player.save()

        Transaction.objects.create(
            player=player,
            amount=amount,
            transaction_type=1
        )

    return Response({'message': 'Баланс успішно поповнено', 'new_balance': player.balance})


@api_view(['POST'])
def place_bet(request):
    player_id = request.data.get('userId')
    match_id = request.data.get('matchId')
    amount = Decimal(request.data.get('amount', 0))
    predicted_result = request.data.get('predictedResult')

    try:
        player = Player.objects.get(id=player_id)
        match = Match.objects.get(id=match_id)
    except (Player.DoesNotExist, Match.DoesNotExist):
        return Response({'error': 'Користувача або матч не знайдено'}, status=status.HTTP_404_NOT_FOUND)

    if player.balance < amount:
        return Response({'error': 'Недостатньо коштів на балансі'}, status=status.HTTP_400_BAD_REQUEST)

    if match.status != 0:
        return Response({'error': 'Ставки на цей матч вже закриті'}, status=status.HTTP_400_BAD_REQUEST)

    # Фиксируем коэффициент
    placed_odds = 0
    if predicted_result == 1:
        placed_odds = match.odds_team1
    elif predicted_result == 2:
        placed_odds = match.odds_team2
    elif predicted_result == 3:
        placed_odds = match.odds_draw

    if placed_odds == 0:
        return Response({'error': 'Невірний вибір результату'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        player.balance -= amount
        player.save()

        Bet.objects.create(
            player=player,
            match=match,
            amount=amount,
            placed_odds=placed_odds,
            predicted_result=predicted_result,
            status=0  # Ожидает
        )

        Transaction.objects.create(
            player=player,
            amount=-amount,
            transaction_type=2  # 2 = Ставка
        )

    return Response({'message': 'Ставку успішно прийнято!', 'remaining_balance': player.balance})

def index_page(request):
    return render(request, 'index.html')