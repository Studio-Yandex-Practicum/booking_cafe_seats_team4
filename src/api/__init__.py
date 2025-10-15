from fastapi import APIRouter

from .endpoints import auth as auth_router
from .endpoints import booking as booking_router
from .endpoints import cafe as cafe_router
from .endpoints import slots as slots_router
from .endpoints import table as table_router
from .endpoints import users as users_router

api_router = APIRouter()
api_router.include_router(auth_router.router)
api_router.include_router(users_router.router)
api_router.include_router(cafe_router.router)
api_router.include_router(table_router.router)
api_router.include_router(slots_router.router)
api_router.include_router(booking_router.router)

__all__ = ['api_router']
