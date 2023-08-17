from aiogram import Router, Dispatcher, F, types
from aiogram.filters.command import Command, CommandObject
from aiogram.enums.dice_emoji import DiceEmoji

from src.database import users, games, referrals, get_total_users_count, get_total_games_count
from src.keyboards.user import InlineKeyboards, ReplyKeyboards
from src.messages.user import Messages
from src.filters import ChatTypeFilter


# region Utils

async def create_user(start_message: types.Message, command: CommandObject):
    name = start_message.from_user.first_name
    username = start_message.from_user.username
    is_user_created = await users.create_user_if_not_exists(
        first_name=name, username=username, telegram_id=start_message.from_user.id
    )

    if is_user_created and command.args and len(command.args.split()) == 1 and command.args.split()[0].isdigit():
        referral_code = int(command.args.split()[0])
        await referrals.add_referral(referrer_telegram_id=referral_code, referral_telegram_id=start_message.from_user.id)

# endregion


# region Handlers

async def handle_start_command(message: types.Message, command: CommandObject):
    await message.answer(text=await Messages.get_welcome(message.from_user.first_name),
                         reply_markup=await ReplyKeyboards.get_menu(),
                         parse_mode='HTML')
    await create_user(start_message=message, command=command)


async def handle_profile_button(message: types.Message):
    user_info = await users.get_user_obj(message.from_user.id)
    await message.answer(text=await Messages.get_user_profile(user_info),
                         reply_markup=await InlineKeyboards.get_profile_markup(),
                         parse_mode='HTML')


async def handle_play_button(message: types.Message):
    available_games = await games.get_available_games()
    await message.answer(text=await Messages.get_play_menu(await users.get_user_obj(message.from_user.id)),
                         reply_markup=await InlineKeyboards.get_games(available_games),
                         parse_mode='HTML')


async def handle_information_button(message: types.Message):
    text = await Messages.get_information( await get_total_users_count(), await get_total_games_count())
    await message.answer(text=text,
                         reply_markup=await InlineKeyboards.get_information_markup(),
                         parse_mode='HTML')


async def handle_referral_system_callback(callback: types.CallbackQuery):
    referrals_count = await referrals.get_referrals_count_of_user(callback.from_user.id)

    text = await Messages.get_referral_system(
        user_telegram_id=callback.from_user.id,
        referrals_count=referrals_count,
        bot_username=(await callback.bot.get_me()).username
    )
    markup = await InlineKeyboards.get_referrals_markup(
        bot_username=(await callback.bot.get_me()).username,
        user_telegram_id=callback.from_user.id
    )

    await callback.message.edit_text(text=text, reply_markup=markup, parse_mode='HTML')

# endregion


def register_private_handlers(router: Dispatcher | Router):
    router.message.filter(ChatTypeFilter('private'))

    router.message.register(handle_start_command, Command('start'))

    router.message.register(handle_play_button, F.text.contains('🎰  Играть  🎰'))
    router.message.register(handle_profile_button, F.text.contains('👤 Профиль'))
    router.message.register(handle_information_button, F.text.contains('ℹ Информация'))

    router.callback_query.register(handle_referral_system_callback, F.data == "referral_system")
