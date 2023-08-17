from tortoise.exceptions import DoesNotExist

from .models import Referral, User
from src.utils import logger


async def get_referrals_count_of_user(telegram_id: int) -> int:
    try:
        user = await User.get(telegram_id=telegram_id)
        referrals = await user.referrals
        return len([referral for referral in referrals])
    except DoesNotExist:
        return 0


async def get_referrer_of_user(telegram_id: int) -> User | None:
    try:
        # !!! Возможно, заменить на ReverseRelation
        user = await User.get(telegram_id=telegram_id)
        referral = await Referral.get(referred_user=user)
        return referral.referrer
    except DoesNotExist:
        return None
    except Exception as e:
        logger.exception(e)


async def add_referral(referral_telegram_id: int, referrer_telegram_id: int) -> bool:
    try:
        referral = await User.get(telegram_id=referral_telegram_id)
        referrer = await User.get(telegram_id=referrer_telegram_id)

        referral, created = await Referral.get_or_create(referred_user=referral, defaults={'referrer': referrer})
        return True if created else False
    except DoesNotExist:
        return False
    except Exception as e:
        logger.exception(e)



