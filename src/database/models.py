from aiogram import html
from tortoise.models import Model
from tortoise import fields

from src.misc import GameStatus, GameType, GameCategory, TransactionType


class User(Model):
    telegram_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=32)
    username = fields.CharField(max_length=32)
    balance = fields.DecimalField(max_digits=6, decimal_places=2)
    registration_date = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        """Возвращает текст со ссылкой-упоминанием юзера в html"""
        link = f"tg://user?id={self.telegram_id}"
        mention = f'{html.link(self.name, link=link)}'
        return mention

    class Meta:
        table = "users"


class Game(Model):
    number = fields.IntField(pk=True, generated=True)
    bet = fields.FloatField()
    max_players = fields.SmallIntField()
    players = fields.ManyToManyField('models.User', related_name='games_participated')
    chat_id = fields.BigIntField(null=True)
    message_id = fields.BigIntField(null=True)
    category = fields.CharEnumField(enum_type=GameCategory, max_length=10)
    game_type = fields.CharEnumField(enum_type=GameType, max_length=1)
    status = fields.IntEnumField(enum_type=GameStatus, description=str(GameStatus))
    start_time = fields.DatetimeField(auto_now_add=True)

    def __str__(self):
        return f'Игра {self.game_type.value}№{self.number}'

    class Meta:
        table = "games"


class PlayerScore(Model):
    game = fields.ForeignKeyField('models.Game', related_name='moves')
    player = fields.ForeignKeyField('models.User', related_name='moves')
    value = fields.SmallIntField()

    class Meta:
        table = "player_scores"


class BlackjackPlayerCard(Model):
    game = fields.ForeignKeyField('models.Game', related_name='blackjack_moves')
    player_id = fields.BigIntField()
    points = fields.SmallIntField()
    suit = fields.CharField(max_length=6)
    value = fields.CharField(max_length=6)

    def __str__(self):
        return f'Карта {self.value}{self.suit}, {self.points} очков'

    class Meta:
        table = "blackjack_player_cards"


class Referral(Model):
    referrer = fields.ForeignKeyField('models.User', related_name='referred_by')  # тот, кто пригласил
    referred_user = fields.ForeignKeyField('models.User', related_name='referrals')  # кого пригласили

    def __str__(self):
        return f'Реферал {self.referred_user} от {self.referrer}'

    class Meta:
        table = "referrals"


class Transaction(Model):
    id = fields.BigIntField(pk=True, generated=True)
    recipient = fields.ForeignKeyField('models.User', related_name='received_transactions')
    sender = fields.ForeignKeyField('models.User', related_name='sent_transactions', null=True)
    game = fields.ForeignKeyField('models.Game', related_name='transactions', null=True)
    amount = fields.DecimalField(max_digits=6, decimal_places=2)
    type = fields.CharEnumField(enum_type=TransactionType, max_length=8)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "transactions"
