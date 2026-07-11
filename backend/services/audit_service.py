from extensions import db
from models import AuditLog

def audit(user_id, action, table_name, record_id=None, old_data=None, new_data=None):
    """Append an audit event to the current transaction."""
    db.session.add(AuditLog(user_id=user_id, action=action, table_name=table_name,
                            record_id=record_id, old_data=old_data, new_data=new_data))
