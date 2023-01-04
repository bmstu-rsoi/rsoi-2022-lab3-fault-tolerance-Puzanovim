import enum
from typing import Dict

from gateway_service.exceptions import ValidationError


def validate_page_size_params(page: int, size: int) -> None:
    if not 0 <= page:
        raise ValidationError('Page should not be less then 0')
    if not 1 <= size <= 100:
        raise ValidationError('Size should be between 1 and 100')


def json_dump(obj: Dict) -> Dict:
    valid_json: Dict[str, str] = {}

    for k, v in obj.items():
        if isinstance(v, enum.Enum):
            v = v.value
        else:
            v = str(v)
        valid_json[k] = v

    return valid_json
