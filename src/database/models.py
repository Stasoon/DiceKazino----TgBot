from aiogram import html
from tortoise import fields
from tortoise.models import Model

from src.misc import GameStatus, GameType, GameCategory
from src.misc.enums.leagues import BandLeague


# region User

class User(Model):
    telegram_id = fields.BigIntField(pk=True)
    name = fields.CharField(max_length=32)
    username = fields.CharField(max_length=32)
    balance = fields.DecimalField(max_digits=12, decimal_places=2)
    referred_by = fields.ForeignKeyField('models.User', related_name='referrals', null=True)
    registration_date = fields.DatetimeField(auto_now_add=True)

    def get_mention_url(self):
        return f"tg://user?id={self.telegram_id}"

    def __str__(self):
        """Возвращает текст со ссылкой-упоминанием юзера в html"""
        link = self.get_mention_url()
        mention = f'{html.link(self.name, link=link)}'
        return mention

    class Meta:
        table = "users"


class BandMember(Model):
    user = fields.ForeignKeyField(model_name="models.User", related_name="band_members")
    band = fields.ForeignKeyField(model_name="models.Band", related_name="band_members")
    score = fields.DecimalField(max_digits=12, decimal_places=2, default=0)


class Band(Model):
    id = fields.BigIntField(pk=True, generated=True, unique=True)
    title = fields.CharField(max_length=50, unique=True)
    league = fields.IntEnumField(enum_type=BandLeague)
    creator = fields.ForeignKeyField(model_name="models.User", related_name="created_band", null=True, on_delete=fields.CASCADE)
    score = fields.DecimalField(max_digits=12, decimal_places=2, default=0)
    members = fields.ManyToManyField('models.User', through='bandmember', related_name='bands')

    def __str__(self):
        return f'Банда {self.title}'


# endregion

# region Games


class Game(Model):
    number = fields.BigIntField(pk=True, generated=True, unique=True)
    bet = fields.FloatField()
    max_players = fields.SmallIntField()
    creator = fields.ForeignKeyField('models.User', related_name='games_creator')
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


class PlayingCard(Model):
    game = fields.ForeignKeyField('models.Game', related_name='playing_cards')
    player_id = fields.BigIntField()
    points = fields.SmallIntField()
    suit = fields.CharField(max_length=6)
    value = fields.CharField(max_length=6)

    def __str__(self):
        return f'Карта {self.value}{self.suit}, {self.points} очков'

    class Meta:
        table = "playing_cards"


class EvenUnevenPlayerBet(Model):
    player = fields.ForeignKeyField('models.User', related_name='even_uneven_player_bet')
    amount = fields.FloatField()
    option = fields.CharField(max_length=1)

    class Meta:
        table = "even_uneven_player_bet"


# endregion


# region Transactions

class Bonus(Model):
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    activation_code = fields.CharField(max_length=20, unique=True)
    available_activations_count = fields.IntField()  # сколько раз доступна активация
    timestamp = fields.DatetimeField(auto_now_add=True)
    is_active = fields.BooleanField(default=True)

    def __str__(self):
        return f'Бонус на {self.amount} ₽ \n' \
               f'Создан: {self.timestamp} \n' \
               f'Активационный код: {self.activation_code} \n'

    class Meta:
        table = "bonuses"


class BonusActivation(Model):
    user = fields.ForeignKeyField('models.User', related_name='bonus_activations')
    bonus = fields.ForeignKeyField('models.Bonus', related_name='activations')


class ReferralBonus(Model):
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    recipient = fields.ForeignKeyField('models.User', related_name='received_referral_bonuses')
    referral = fields.ForeignKeyField('models.User', related_name='referral_bonuses_given')
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "referral_bonus"


class Deposit(Model):
    """Пополнения балансов"""
    id = fields.BigIntField(pk=True, generated=True)
    user = fields.ForeignKeyField('models.User', related_name='user_deposits')
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "deposits"


class Withdraw(Model):
    """Выводы средств с балансов"""
    id = fields.BigIntField(pk=True, generated=True)
    user = fields.ForeignKeyField('models.User', related_name='user_withdraws')
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "withdraws"


class Bet(Model):
    """Ставки в играх"""
    id = fields.BigIntField(pk=True, generated=True)
    user = fields.ForeignKeyField('models.User', related_name='user_bets')
    game = fields.ForeignKeyField('models.Game', related_name='game_bets', null=True)
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "bets"


class Winning(Model):
    """Выигрыши в играх"""
    id = fields.BigIntField(pk=True, generated=True)
    user = fields.ForeignKeyField('models.User', related_name='user_winnings')
    game_category = fields.CharEnumField(enum_type=GameCategory, description='game_winnings')
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "winnings"


class BetRefund(Model):
    """Возврат ставки в игре"""
    id = fields.BigIntField(pk=True, generated=True)
    user = fields.ForeignKeyField('models.User', related_name='user_refunds')
    game = fields.ForeignKeyField('models.Game', related_name='game_refunds', null=True)
    amount = fields.DecimalField(max_digits=10, decimal_places=2)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "bet_refunds"


# endregion
