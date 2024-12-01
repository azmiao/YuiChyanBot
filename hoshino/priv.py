
from yuiChyan.permission import *


def get_user_priv(ev):
    return get_user_permission(ev)


def check_priv(ev, require):
    return check_permission(ev, require)
