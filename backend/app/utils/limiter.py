"""Rate limiting utility — re-exported from main.py limiter."""
# Rate limiting is handled by slowapi configured in main.py
# This module exists for future custom rate limiting logic per endpoint.

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
