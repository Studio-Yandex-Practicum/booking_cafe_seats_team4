from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.exceptions import err
from api.validators.auth import authenticate_user
from core.db import get_session
from core.security import create_access_token
from schemas.auth import AuthData, AuthToken

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
    try:
        user = await authenticate_user(session, form.login, form.password)
    except HTTPException as e:
        # По OpenAPI: неверные 422, неактивный 403
        if e.status_code == 401:
            raise err(
                'AUTH_INVALID_CREDENTIALS',
                'Неверный логин или пароль',
                422,
            )
        if e.status_code == 403:
            raise err(
                'AUTH_INACTIVE_USER',
                'Пользователь неактивен',
                403,
            )
        raise

    token = create_access_token(subject=str(user.id))
    return AuthToken(access_token=token, token_type='bearer')
