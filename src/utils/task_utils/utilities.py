
import uuid
import random
from middlewares.errors.error_handler import handle_exceptions


@handle_exceptions
def randomize_timeout(min_timeout, max_timeout):
    increments = 5000
    possible_timeouts = list(range(min_timeout, max_timeout + increments, increments))
    return random.choice(possible_timeouts)


def generate_uuid():
    return str(uuid.uuid4())
