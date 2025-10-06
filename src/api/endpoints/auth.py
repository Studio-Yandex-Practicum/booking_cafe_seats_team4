from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.validators.auth import authenticate_user
from src.core.db import get_session
from src.core.security import create_access_token
from src.schemas.auth import AuthData, AuthToken

router = APIRouter(prefix='/auth', tags=['Аутентификация'])


@router.post(
    '/login',
    response_model=AuthToken,
    summary='Вход',
)
async def login(
    form: Annotated[AuthData, Depends(AuthData.as_form)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthToken:
    """Авторизация пользователя по логину и паролю."""
    user = await authenticate_user(session, form.login, form.password)
    token = create_access_token(subject=str(user.id))
    return AuthToken(access_token=token, token_type='bearer')
