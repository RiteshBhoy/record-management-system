from datetime import datetime, timezone
from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

def iso(value):
    """Serialize datetime safely."""
    return value.isoformat() if value else None

def success(message, data=None, status=200):
    """Return a standardized successful API response."""
    return jsonify({"success": True, "status_code": status, "message": message,
                    "data": data, "timestamp": datetime.now(timezone.utc).isoformat()}), status

def pydantic_errors(exc: PydanticValidationError):
    """Convert Pydantic errors to field-keyed safe messages."""
    errors = {}
    for item in exc.errors():
        field = ".".join(str(x) for x in item["loc"])
        errors.setdefault(field, []).append(item["msg"].replace("Value error, ", ""))
    return errors

def record_dict(r):
    """Serialize a record for APIs."""
    fields = ["id","record_id","client_id","status","is_locked","version","name","age","sex",
              "fees","email","phone","address","city","state","country","occupation",
              "blood_group","nationality","marital_status","aadhaar","pan","remarks",
              "validation_status","created_at","updated_at","approved_at"]
    result = {f: getattr(r, f) for f in fields}
    for f in ("created_at","updated_at","approved_at"): result[f] = iso(result[f])
    return result
