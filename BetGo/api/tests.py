from django.test import TestCase
from rest_framework.test import APIClient
from decimal import Decimal

from .models import Player, Match, Bet, Transaction


def make_player(username='testuser', password='pass123', balance=1000):
    return Player.objects.create(username=username, password=password, balance=balance)

def make_match():
    return Match.objects.create(
        team1_name='Team A', team2_name='Team B',
        odds_team1=2.0, odds_team2=3.0, odds_draw=3.5
    )


class BettingTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.player = make_player()
        self.match = make_match()

    def test_register_success(self):
        res = self.client.post('/api/players/', {'username': 'alice', 'password': '1234'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Player.objects.filter(username='alice').exists())

    def test_place_bet_deducts_balance(self):
        self.client.post('/api/bets/place/', {
            'userId': self.player.id, 'matchId': self.match.id,
            'amount': 200, 'predictedResult': 1
        }, format='json')
        self.player.refresh_from_db()
        self.assertEqual(self.player.balance, Decimal('800'))

    def test_place_bet_insufficient_balance(self):
        res = self.client.post('/api/bets/place/', {
            'userId': self.player.id, 'matchId': self.match.id,
            'amount': 9999, 'predictedResult': 1
        }, format='json')
        self.assertEqual(res.status_code, 400)

    def test_winning_bet_pays_out(self):
        self.client.post('/api/bets/place/', {
            'userId': self.player.id, 'matchId': self.match.id,
            'amount': 100, 'predictedResult': 1
        }, format='json')
        self.client.post(f'/api/matches/{self.match.id}/finish/', {'result': 1}, format='json')
        self.player.refresh_from_db()
        # 1000 - 100+ 100 * 2.0 = 1100
        self.assertEqual(self.player.balance, Decimal('1100'))

    def test_promo_freebet_gives_bonus(self):
        player = make_player(username='newuser', balance=0)
        res = self.client.post(f'/api/users/{player.id}/top-up/', {
            'amount': 100, 'promoCode': 'FREEBET'
        }, format='json')
        self.assertEqual(res.status_code, 200)
        player.refresh_from_db()
        self.assertEqual(player.balance, Decimal('600'))