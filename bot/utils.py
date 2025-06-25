# Utilidades generales para el bot

def safe_get(d, key, default=None):
    try:
        return d[key]
    except (KeyError, TypeError):
        return default
