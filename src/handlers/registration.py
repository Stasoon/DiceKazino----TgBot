from aiogram import Dispatcher, Router

from .user import register_user_handlers
# from .admin import register_admin_handlers


def register_all_handlers(dp: Dispatcher):
    user_router = Router(name='user_router')
    register_user_handlers(user_router)

    admin_router = Router(name='admin_router')

    dp.include_routers(user_router, admin_router)
