from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

ErrorCodeStr = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        pattern=r'^[A-Z0-9_]+$',
    ),
]

ErrorMessageStr = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


class ErrorResponse(BaseModel):
    """Стандартизированная схема ответа об ошибке."""

    model_config = ConfigDict(frozen=True)

    code: ErrorCodeStr
    message: ErrorMessageStr
