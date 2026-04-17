_states: dict[int, str] = {}

# Константы состояний
WAITING_FOR_UON_ID = "waiting_for_uon_id"


def get_state(user_id: int) -> str | None:
    # какой щас стейт
    return _states.get(user_id)


def set_state(user_id: int, state: str) -> None:
    _states[user_id] = state


def clear_state(user_id: int) -> None:
    _states.pop(user_id, None)
