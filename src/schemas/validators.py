from datetime import date


def validate_date_not_past(booking_date: date) -> date:
    """Проверка, что дата бронирования не в прошлом."""
    if booking_date < date.today():
        raise ValueError('Нельзя бронировать на прошедшие даты')
    return booking_date


def validate_positive_number(value: int, field_name: str = 'Значение') -> int:
    """Проверка, что значение положительное."""
    if value <= 0:
        raise ValueError(f'{field_name} должно быть положительным')
    return value


def validate_time_format(time_str: str) -> str:
    """Проверка формата времени (HH:MM)."""
    from datetime import datetime

    try:
        datetime.strptime(time_str, '%H:%M')
        return time_str
    except ValueError:
        raise ValueError('Время должно быть в формате HH:MM')


def validate_time_range(start_time: str, end_time: str) -> tuple[str, str]:
    """Проверка, что время окончания не раньше времени начала."""
    from datetime import datetime

    start = datetime.strptime(start_time, '%H:%M')
    end = datetime.strptime(end_time, '%H:%M')
    if end <= start:
        raise ValueError('Время окончания должно быть позже времени начала')
    return start_time, end_time
