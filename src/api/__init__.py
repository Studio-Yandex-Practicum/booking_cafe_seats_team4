from fastapi import APIRouter

from .endpoints import auth as auth_router
from .endpoints import users as users_router
from .endpoints import slots as slots_router
from .endpoints import dishes as dishes_router
from .endpoints import actions as actions_router

api_router = APIRouter()
api_router.include_router(auth_router.router)
api_router.include_router(users_router.router)
api_router.include_router(slots_router.router)
api_router.include_router(dishes_router.router)
api_router.include_router(actions_router.router)

__all__ = ['api_router']
