BOOKING_CONFIRMATION_TEMPLATE = """
Уважаемый(ая) {username},

У вас забронирован стол.

Дата: {booking_date}
Кафе: {cafe}
Время: {first_slot} - {last_slot}
"""

ACTION_TEMPLATE = """
Уважаемый пользователь!
У нас новая акция: {action_description}
"""

BOOKING_INFORMATION_FOR_MANAGER = """
Новое бронирование в кафе {cafe}

Дата: {booking_date}
Время: {first_slot} - {last_slot}
Стол: {table}
"""
