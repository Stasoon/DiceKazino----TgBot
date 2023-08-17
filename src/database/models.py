from typing import List

from aiogram import html
from tortoise.models import Model
from tortoise import fields

from src.misc import GameStatus, GameType


class User(Model):
    telegram_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=32)
    username = fields.CharField(max_length=32)
    balance = fields.DecimalField(max_digits=6, decimal_places=2)
    registration_date = fields.DatetimeField(auto_now_add=True)
    bot_blocked = fields.BooleanField(default=False)

    def __str__(self):
        """Возвращает упоминание юзера"""
        link = f"tg://user?id={self.telegram_id}"
        mention = f'{html.link(self.name, link=link)}'
        return mention


class Game(Model):
    number = fields.IntField(pk=True, generated=True)
    bet = fields.FloatField()
    max_players = fields.SmallIntField()
    players = fields.ManyToManyField('models.User', related_name='games_participated')
    winner = fields.ForeignKeyField('models.User', related_name='games_won', null=True)
    type = fields.CharEnumField(enum_type=GameType, max_length=1)
    status = fields.IntEnumField(enum_type=GameStatus, description=str(GameStatus))

    def __str__(self):
        return f'Игра {self.type.value}№{self.number}'


class PlayerMove(Model):
    game = fields.ForeignKeyField('models.Game', related_name='moves')
    player = fields.ForeignKeyField('models.User', related_name='moves')
    value = fields.SmallIntField()


class Referral(Model):
    referrer = fields.ForeignKeyField('models.User', related_name='referred_by')
    referred_user = fields.ForeignKeyField('models.User', related_name='referrals')

    def __str__(self):
        return f'Referral from {self.referrer} to {self.referred_user}'


class Transaction(Model):
    pass
