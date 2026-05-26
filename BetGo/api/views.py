from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from decimal import Decimal

from .models import Player, Match, Bet, Transaction, Tag, MatchTag
from django.shortcuts import render


@api_view(['POST'])
def create_player(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({'error': 'Логін та пароль обов\'язкові'}, status=status.HTTP_400_BAD_REQUEST)

    if Player.objects.filter(username=username).exists():
        return Response({'error': 'Користувач з таким ім\'ям вже існує'}, status=status.HTTP_400_BAD_REQUEST)

    player = Player.objects.create(username=username, password=password, balance=0)
    return Response({'message': 'Гравця створено', 'playerId': player.id}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def login_player(request):
    username = request.data.get('username')
    password = request.data.get('password')
    try:
        player = Player.objects.get(username=username, password=password)
        return Response({'message': 'Авторизація успішна', 'playerId': player.id, 'username': player.username, 'balance': player.balance})
    except Player.DoesNotExist:
        return Response({'error': 'Невірний логін або пароль'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def get_player(request, player_id):
    try:
        player = Player.objects.get(id=player_id)

        bets = player.bets.select_related('match').order_by('-id')
        bets_data = [{
            'id': b.id,
            'matchName': f"{b.match.team1_name} vs {b.match.team2_name}",
            'amount': b.amount,
            'placedOdds': b.placed_odds,
            'predictedResult': b.predicted_result,
            'status': b.status
        } for b in bets]

        transactions = player.transactions.order_by('-id')
        tx_data = [{
            'id': t.id,
            'amount': t.amount,
            'type': t.transaction_type,
            'date': t.created_at.strftime("%d.%m.%Y %H:%M")
        } for t in transactions]

        return Response({
            'id': player.id,
            'username': player.username,
            'balance': player.balance,
            'bets': bets_data,
            'transactions': tx_data
        })
    except Player.DoesNotExist:
        return Response({'error': 'Користувача не знайдено'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def create_match(request):
    team1 = request.data.get('team1Name')
    team2 = request.data.get('team2Name')
    category_name = request.data.get('category', 'Інше')

    if not team1 or not team2:
        return Response({'error': 'Назви команд обов\'язкові'}, status=status.HTTP_400_BAD_REQUEST)

    match = Match.objects.create(
        team1_name=team1,
        team2_name=team2,
        odds_team1=request.data.get('oddsTeam1', 1.5),
        odds_team2=request.data.get('oddsTeam2', 1.5),
        odds_draw=request.data.get('oddsDraw', 3.0)
    )

    tag, _ = Tag.objects.get_or_create(name=category_name)
    MatchTag.objects.create(match=match, tag=tag)

    return Response({'message': 'Матч створено', 'matchId': match.id}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def list_matches(request):
    matches = Match.objects.filter(status=Match.Status.ACTIVE).prefetch_related('tags').order_by('-id')
    data = []
    for m in matches:
        category = m.tags.first().name if m.tags.exists() else 'Інше'
        data.append({
            'id': m.id,
            'team1Name': m.team1_name,
            'team2Name': m.team2_name,
            'oddsTeam1': m.odds_team1,
            'oddsTeam2': m.odds_team2,
            'oddsDraw': m.odds_draw,
            'status': m.status,
            'category': category
        })
    return Response(data)


@api_view(['POST'])
def top_up_balance(request, player_id):
    amount = request.data.get('amount')
    promo = request.data.get('promoCode', '').strip().upper()

    if not amount or Decimal(str(amount)) <= 0:
        return Response({'error': 'Сума поповнення має бути більшою за нуль'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        player = Player.objects.get(id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Користувача не знайдено'}, status=status.HTTP_404_NOT_FOUND)

    bonus_amount = Decimal('0.00')
    if promo == 'FREEBET':
        has_used_bonus = Transaction.objects.filter(
            player=player,
            transaction_type=Transaction.Type.BONUS
        ).exists()

        if has_used_bonus:
            return Response({'error': 'Ви вже використали цей промокод раніше!'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            bonus_amount = Decimal('500.00')
    elif promo != '':
        return Response({'error': 'Невірний промокод'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        player.balance += Decimal(str(amount))
        Transaction.objects.create(player=player, amount=amount, transaction_type=Transaction.Type.DEPOSIT)

        if bonus_amount > 0:
            player.balance += bonus_amount
            Transaction.objects.create(player=player, amount=bonus_amount, transaction_type=Transaction.Type.BONUS)

        player.save()

    msg = 'Баланс успішно поповнено'
    if bonus_amount > 0:
        msg += f' (+{bonus_amount}₴ бонус!)'

    return Response({'message': msg, 'new_balance': player.balance})


@api_view(['POST'])
def withdraw_money(request, player_id):
    amount = request.data.get('amount')

    if not amount or Decimal(str(amount)) <= 0:
        return Response({'error': 'Сума виведення має бути більшою за нуль'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        player = Player.objects.get(id=player_id)
    except Player.DoesNotExist:
        return Response({'error': 'Користувача не знайдено'}, status=status.HTTP_404_NOT_FOUND)

    withdraw_amount = Decimal(str(amount))

    if player.balance < withdraw_amount:
        return Response({'error': 'Недостатньо коштів для виведення'}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        player.balance -= withdraw_amount
        player.save()
        Transaction.objects.create(player=player, amount=-withdraw_amount, transaction_type=Transaction.Type.WITHDRAWAL)

    return Response({'message': 'Кошти успішно виведено', 'new_balance': player.balance})


@api_view(['POST'])
def place_bet(request):
    player_id = request.data.get('userId')
    match_id = request.data.get('matchId')
    amount = Decimal(str(request.data.get('amount', 0)))
    predicted_result = request.data.get('predictedResult')

    if amount <= 0:
        return Response({'error': 'Сума ставки має бути більшою за нуль'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        player = Player.objects.get(id=player_id)
        match = Match.objects.get(id=match_id)
    except (Player.DoesNotExist, Match.DoesNotExist):
        return Response({'error': 'Користувача або матч не знайдено'}, status=status.HTTP_404_NOT_FOUND)

    if player.balance < amount:
        return Response({'error': 'Недостатньо коштів на балансі'}, status=status.HTTP_400_BAD_REQUEST)
    if match.status != Match.Status.ACTIVE:
        return Response({'error': 'Ставки на цей матч вже закриті'}, status=status.HTTP_400_BAD_REQUEST)

    odds_map = {
        Bet.PredictedResult.TEAM1_WIN: match.odds_team1,
        Bet.PredictedResult.TEAM2_WIN: match.odds_team2,
        Bet.PredictedResult.DRAW:      match.odds_draw,
    }
    placed_odds = odds_map.get(predicted_result)
    if placed_odds is None:
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
            status=Bet.Status.PENDING
        )
        Transaction.objects.create(player=player, amount=-amount, transaction_type=Transaction.Type.BET)

    return Response({'message': 'Ставку успішно прийнято!', 'remaining_balance': player.balance})


def index_page(request):
    return render(request, 'index.html')


@api_view(['POST'])
def finish_match(request, match_id):
    winning_result = request.data.get('result')  # Bet.PredictedResult: 1, 2 або 3

    if winning_result not in [
        Bet.PredictedResult.TEAM1_WIN,
        Bet.PredictedResult.TEAM2_WIN,
        Bet.PredictedResult.DRAW,
    ]:
        return Response({'error': 'Невірний результат матчу'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        match = Match.objects.get(id=match_id, status=Match.Status.ACTIVE)
    except Match.DoesNotExist:
        return Response({'error': 'Матч не знайдено або він вже завершений'}, status=status.HTTP_404_NOT_FOUND)

    with transaction.atomic():
        match.status = Match.Status.FINISHED
        match.result = winning_result
        match.save()

        bets = Bet.objects.filter(match=match, status=Bet.Status.PENDING)

        for bet in bets:
            if bet.predicted_result == winning_result:
                bet.status = Bet.Status.WON
                win_amount = bet.amount * bet.placed_odds

                player = bet.player
                player.balance += win_amount
                player.save()

                Transaction.objects.create(player=player, amount=win_amount, transaction_type=Transaction.Type.WIN)
            else:
                bet.status = Bet.Status.LOST

            bet.save()

    return Response({'message': 'Матч успішно завершено! Всі ставки розраховано.'})