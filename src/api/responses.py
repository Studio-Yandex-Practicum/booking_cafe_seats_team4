from schemas.common import ErrorResponse

SUCCESSFUL_RESPONSE = {
    200: {'description': 'Успешно'},
}

NOT_FOUND_RESPONSE = {
    404: {
        'description': 'Запрашиваемый ресурс не найден',
        'content': {
            'application/json': {
                'schema': ErrorResponse.model_json_schema(),
                'example': {
                    'code': 'NOT_FOUND',
                    'message': 'Ресурс не найден',
                },
            },
        },
    },
}

FORBIDDEN_RESPONSE = {
    403: {
        'description': 'Доступ запрещен (недостаточно прав)',
        'content': {
            'application/json': {
                'schema': ErrorResponse.model_json_schema(),
                'example': {
                    'code': 'FORBIDDEN',
                    'message': 'Недостаточно прав',
                },
            },
        },
    },
}

UNAUTHORIZED_RESPONSE = {
    401: {
        'description': 'Ошибка аутентификации',
        'content': {
            'application/json': {
                'schema': ErrorResponse.model_json_schema(),
                'example': {
                    'code': 'UNAUTHORIZED',
                    'message': 'Требуется авторизация',
                },
            },
        },
    },
}

VALIDATION_ERROR_RESPONSE = {
    422: {
        'description': 'Ошибка валидации данных',
        'content': {
            'application/json': {
                'schema': ErrorResponse.model_json_schema(),
                'example': {
                    'code': 'VALIDATION_ERROR',
                    'message': 'Неверные данные запроса',
                },
            },
        },
    },
}


CAFE_DUPLICATE_RESPONSE = {
    400: {
        'description': 'Попытка создать дубликат кафе',
        'content': {
            'application/json': {
                'schema': ErrorResponse.model_json_schema(),
                'example': {
                    'code': 'CAFE_DUPLICATE',
                    'message': (
                        'Кафе с таким названием и адресом уже существует.'
                    ),
                },
            },
        },
    },
}

INVALID_MANAGER_ID_RESPONSE = {
    400: {
        'description': 'Указан неверный ID менеджера',
        'content': {
            'application/json': {
                'schema': ErrorResponse.model_json_schema(),
                'example': {
                    'code': 'INVALID_MANAGER_ID',
                    'message': 'Один или несколько ID менеджеров не найдены',
                },
            },
        },
    },
}

INVALID_ID_RESPONSE = {
    400: {
        'description': 'Неверный формат или значение ID',
        'content': {
            'application/json': {
                'schema': ErrorResponse.model_json_schema(),
                'example': {
                    'code': 'INVALID_ID_FORMAT',
                    'message': 'ID должен быть положительным числом',
                },
            },
        },
    },
}

TABLE_NOT_FOUND_IN_CAFE_RESPONSE = {
    404: {
        'description': 'Стол не найден в указанном кафе',
        'content': {
            'application/json': {
                'schema': ErrorResponse.model_json_schema(),
                'example': {
                    'code': 'NOT_FOUND',
                    'message': 'Стол не найден в данном кафе',
                },
            },
        },
    },
}
