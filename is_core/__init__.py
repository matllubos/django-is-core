from .models.patch import *


VERSION = (0, 3, 22)


def get_version():
    return '.'.join(map(str, VERSION))
