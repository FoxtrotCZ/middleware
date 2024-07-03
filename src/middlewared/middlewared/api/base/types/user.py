import string

from annotated_types import Ge, Le
from pydantic.functional_validators import AfterValidator
from typing_extensions import Annotated

__all__ = ["LocalUsername", "RemoteUsername", "LocalUID"]

TRUENAS_IDMAP_DEFAULT_LOW = 90000001

DEFAULT_VALID_CHARS = string.ascii_letters + string.digits + '_' + '-' + '$' + '.'
DEFAULT_VALID_START = string.ascii_letters + '_'
DEFAULT_MAX_LENGTH = 32


def validate_username(
    val: str,
    valid_chars: str = DEFAULT_VALID_CHARS,
    valid_start_chars : str | None = DEFAULT_VALID_START,
    max_length: int | None = DEFAULT_MAX_LENGTH
) -> str:
    val_len = len(val)
    assert val_len > 0, 'Username must be at least 1 character in length'
    if max_length is not None:
        assert val_len <= max_length, f'Username cannot exceed {max_length} charaters in length'
    if valid_start_chars is not None:
        assert val[0] in valid_start_chars, 'Username must start with a letter or an underscore'

    assert '$' not in val or val[-1] == '$', 'Username must end with a dollar sign character'
    assert all(char in valid_chars for char in val), f'Valid characters for a username are: {", ".join(valid_chars)!r}'
    return val


def validate_local_username(val: str) -> str:
    # see man 8 useradd, specifically the CAVEATS section
    # NOTE: we are ignoring the man page's recommendation for insistence
    # upon the starting character of a username be a lower-case letter.
    # We aren't enforcing this for maximum backwards compatibility
    return validate_username(val)


def validate_remote_username(val: str) -> str:
    # Restrictions on names returned by nss_winbind are more lax than we place
    # on our local usernames. \\ is used as a separator for domain and username
    return validate_username(val, DEFAULT_VALID_CHARS + '\\', None, None)


LocalUsername = Annotated[str, AfterValidator(validate_local_username)]
RemoteUsername = Annotated[str, AfterValidator(validate_remote_username)]
LocalUID = Annotated[int, Ge(0), Le(TRUENAS_IDMAP_DEFAULT_LOW - 1)]
