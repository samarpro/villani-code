def resolve(default, file_value=None, env_value=None):
    if file_value is not None:
        return file_value
    if env_value is not None:
        return env_value
    return default
