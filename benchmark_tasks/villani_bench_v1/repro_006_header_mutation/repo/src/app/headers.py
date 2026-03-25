def normalize_headers(headers: dict[str, str]) -> dict[str, str]:
    for key in list(headers):
        headers[key.lower()] = headers.pop(key)
    return headers
