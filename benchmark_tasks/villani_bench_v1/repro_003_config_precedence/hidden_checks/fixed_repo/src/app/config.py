def resolve(default, file_value=None, env_value=None):
    if env_value is not None:
        return env_value
    if file_value is not None:
        return file_value
    return default
