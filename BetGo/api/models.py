from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=50)


class Match(models.Model):
    class Status(models.IntegerChoices):
        ACTIVE = 0, 'Активний'
        FINISHED = 1, 'Завершений'

    class Result(models.IntegerChoices):
        NOT_PLAYED = 0, 'Не зіграно'
        TEAM1_WIN = 1, 'Перемога команди 1'
        TEAM2_WIN = 2, 'Перемога команди 2'
        DRAW = 3, 'Нічия'

    team1_name = models.CharField(max_length=100)
    team2_name = models.CharField(max_length=100)
    status = models.IntegerField(choices=Status.choices, default=Status.ACTIVE)
    result = models.IntegerField(choices=Result.choices, default=Result.NOT_PLAYED)
    odds_team1 = models.DecimalField(max_digits=8, decimal_places=2)
    odds_team2 = models.DecimalField(max_digits=8, decimal_places=2)
    odds_draw = models.DecimalField(max_digits=8, decimal_places=2)
    tags = models.ManyToManyField(Tag, through='MatchTag', related_name='matches')


class MatchTag(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)


class Player(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    balance = models.DecimalField(max_digits=18, decimal_places=2, default=0.00)


class Bet(models.Model):
    class Status(models.IntegerChoices):
        PENDING = 0, 'Активна'
        WON = 1, 'Виграна'
        LOST = 2, 'Програна'

    class PredictedResult(models.IntegerChoices):
        TEAM1_WIN = 1, 'Перемога команди 1'
        TEAM2_WIN = 2, 'Перемога команди 2'
        DRAW = 3, 'Нічия'

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='bets')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='bets')
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    placed_odds = models.DecimalField(max_digits=8, decimal_places=2)
    predicted_result = models.IntegerField(choices=PredictedResult.choices)
    status = models.IntegerField(choices=Status.choices, default=Status.PENDING)


class Transaction(models.Model):
    class Type(models.IntegerChoices):
        DEPOSIT = 1, 'Поповнення'
        BET = 2, 'Ставка'
        WITHDRAWAL = 3, 'Виведення'
        BONUS = 4, 'Бонус'
        WIN = 5, 'Виграш'

    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_type = models.IntegerField(choices=Type.choices)
    created_at = models.DateTimeField(auto_now_add=True)