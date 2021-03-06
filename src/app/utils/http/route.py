from typing import Optional

from src.app.routing.router import Router


def _normalize_alias(alias: str) -> Optional[str]:
    if alias is not None and len(alias) > 0:
        return F'/{alias}' if alias[0] != '/' else alias
    return None


def route(method_type: str, alias: str = None, auth_required: bool = True):
    def wrapper(func):
        Router.register_http_method({
            'type': method_type,
            'alias': _normalize_alias(alias),
            'class_name': func.__qualname__.split('.')[0],
            'method_name': func.__name__,
            'auth_required': auth_required
        })
        return func

    return wrapper
