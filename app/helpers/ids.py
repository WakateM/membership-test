"""Generated ids: a random UUID encoded in base 62."""
import uuid

from app.helpers.config import BASE62_ALPHABET


def encode_base62(number: int) -> str:
    """Return the non-negative number written in base 62."""
    base = len(BASE62_ALPHABET)
    digits = []
    while True:
        number, remainder = divmod(number, base)
        digits.append(BASE62_ALPHABET[remainder])
        if number == 0:
            break
    return "".join(reversed(digits))


def generate_base62_id() -> str:
    """Return a new unique id: a random 128-bit UUID written in base 62."""
    random_uuid = uuid.uuid4()
    return encode_base62(random_uuid.int)
