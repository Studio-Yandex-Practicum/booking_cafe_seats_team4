from datetime import date, datetime


def validate_date_not_past(booking_date: date) -> date:
    """Проверка, что дата бронирования не в прошлом."""
    if booking_date < date.today():
        raise ValueError(
            f'Нельзя бронировать на прошедшие даты: {booking_date}',
        )
    return booking_date


def validate_positive_number(value: int, field_name: str = 'Значение') -> int:
    """Проверка, что значение положительное."""
    if value <= 0:
        raise ValueError(
            f'{field_name} должно быть положительным, получено {value}',
        )
    return value


def validate_time_format(time_str: str) -> str:
    """Проверка формата времени (HH:MM)."""
    try:
        datetime.strptime(time_str, '%H:%M')
        return time_str
    except ValueError:
        raise ValueError(
            f'Время должно быть в формате HH:MM, получено "{time_str}"',
        )


def validate_time_range(start_time: str, end_time: str) -> tuple[str, str]:
    """Проверка, что время окончания не раньше времени начала."""
    start = datetime.strptime(start_time, '%H:%M')
    end = datetime.strptime(end_time, '%H:%M')
    if end <= start:
        raise ValueError('Время окончания должно быть позже времени начала')
    return start_time, end_time
