"""Простое in-memory хранилище FSM-состояний пользователей."""

_states: dict[int, str] = {}

# Константы состояний
WAITING_FOR_UON_ID = "waiting_for_uon_id"


def get_state(user_id: int) -> str | None:
    """Возвращает текущее состояние пользователя или None."""
    return _states.get(user_id)


def set_state(user_id: int, state: str) -> None:
    """Устанавливает FSM-состояние для пользователя."""
    _states[user_id] = state


def clear_state(user_id: int) -> None:
    """Сбрасывает FSM-состояние пользователя."""
    _states.pop(user_id, None)
