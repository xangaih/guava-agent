import json
from pathlib import Path

_CUSTOMERS = json.loads(
    (Path(__file__).parent / "data" / "customers.json").read_text()
)
_BY_PHONE = {c["phone"]: c for c in _CUSTOMERS}
_BY_POLICY = {c["policy_number"]: c for c in _CUSTOMERS}


def lookup_by_phone(phone: str) -> dict | None:
    return _BY_PHONE.get(phone)


def lookup_by_policy(policy_number: str) -> dict | None:
    return _BY_POLICY.get(policy_number)
