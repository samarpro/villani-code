def next_delay(status_codes: list[int]) -> float:
    if not status_codes:
        return 0.0
    if status_codes[-1] == 429:
        return 0.5
    return 0.0
