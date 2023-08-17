from aiogram import Router

from .private import register_private_handlers
from .public import register_public_handlers


def register_user_handlers(user_router: Router):
    private_router = Router(name='user_private_router')
    register_private_handlers(private_router)

    public_router = Router(name='user_public_router')
    register_public_handlers(public_router)

    user_router.include_routers(private_router, public_router)
