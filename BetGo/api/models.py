from django.db import models

class Tag(models.Model):
    name = models.CharField(max_length=50)

class Match(models.Model):
    team1_name = models.CharField(max_length=100)
    team2_name = models.CharField(max_length=100)
    status = models.IntegerField(default=0)
    result = models.IntegerField(default=0)
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
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='bets')
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='bets')
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    placed_odds = models.DecimalField(max_digits=8, decimal_places=2)
    predicted_result = models.IntegerField()
    status = models.IntegerField(default=0)

class Transaction(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    transaction_type = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)