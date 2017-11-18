from datetime import datetime
import math
import re

from .types import Reqid

def utcnow_ts():
    return datetime.utcnow().timestamp()

def utcnow_reqid():
    return Reqid(math.floor(utcnow_ts() * 10**9))

def camel_to_snake(name):
    return re.sub('(.)([A-Z])', r'\1_\2', name).lower()
