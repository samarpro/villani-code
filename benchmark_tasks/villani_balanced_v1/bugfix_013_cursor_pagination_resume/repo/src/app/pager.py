from dataclasses import dataclass

@dataclass
class Page:
    items: list[int]
    next_cursor: int | None

def page_after(items: list[int], cursor: int | None, size: int) -> Page:
    start = 0 if cursor is None else cursor + 1
    chunk = items[start:start + size]
    if not chunk:
        return Page([], None)
    next_cursor = start + len(chunk) - 1
    return Page(chunk, next_cursor)
