from flask import make_response
from services.email_service import EmailService
from services.pdf_service import PDFService
from datetime import datetime, timezone
from flask import Blueprint, request
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from extensions import db
from models import MainTable
from schemas import RecordSchema, ActionSchema
from middleware.auth import current_user, roles_required
from services.audit_service import audit
from utils.exceptions import ValidationError, DuplicateRecordError, ResourceNotFoundError, AuthorizationError, BusinessLogicError, DatabaseError
from utils.helpers import success, pydantic_errors, record_dict

records_bp = Blueprint("records", __name__, url_prefix="/api/records")

def find_record(record_id):
    """Find a non-deleted record or raise 404."""
    r = db.session.get(MainTable, record_id)
    if not r or r.is_deleted: raise ResourceNotFoundError("Record not found")
    return r

def validate_record():
    """Validate current JSON request using Pydantic."""
    try: return RecordSchema.model_validate(request.get_json(silent=True) or {})
    except PydanticValidationError as exc: raise ValidationError("Validation Failed", pydantic_errors(exc))

@records_bp.post("")
def create_record():
    """Create and automatically lock a client record."""
    u = current_user()
    data = validate_record()
    if MainTable.query.filter_by(record_id=data.record_id).first(): raise DuplicateRecordError("Duplicate Record ID")
    payload = data.model_dump(mode="json")
    r = MainTable(**payload, client_id=u.id, created_by=u.id, locked_by=u.id,
                  is_locked=True, input_json=payload,
                  extracted_json={**payload, "processed_by":"backend", "version":1})
    try:
        db.session.add(r); audit(u.id, "CREATE", "main_table", r.record_id, None, payload); db.session.commit()
    except IntegrityError as exc:
        db.session.rollback(); raise DuplicateRecordError("Duplicate Record ID") from exc
    except SQLAlchemyError as exc:
        db.session.rollback(); raise DatabaseError("Unable to save record") from exc
    return success("Record created and locked", record_dict(r), 201)

@records_bp.get("")
def list_records():
    """List records with role filtering, pagination, sorting and search."""
    u = current_user()
    page=max(request.args.get("page",1,type=int),1); per=min(max(request.args.get("per_page",10,type=int),1),100)
    q=MainTable.query.filter_by(is_deleted=False)
    if u.role=="CLIENT": q=q.filter_by(client_id=u.id)
    term=request.args.get("search","").strip()
    if term: q=q.filter(MainTable.record_id.contains(term) | MainTable.name.contains(term))
    allowed={"created_at":MainTable.created_at,"record_id":MainTable.record_id,"name":MainTable.name,"status":MainTable.status}
    col=allowed.get(request.args.get("sort"),MainTable.created_at)
    q=q.order_by(col.asc() if request.args.get("order")=="asc" else col.desc())
    p=q.paginate(page=page,per_page=per,error_out=False)
    return success("Records fetched", {"items":[record_dict(x) for x in p.items],"page":p.page,"pages":p.pages,"total":p.total})

@records_bp.get("/search")
def search():
    """Search by exact record ID."""
    u=current_user(); rid=request.args.get("record_id","").strip()
    if not rid: raise ValidationError("Validation Failed", {"record_id":["Record ID is required"]})
    r=MainTable.query.filter_by(record_id=rid,is_deleted=False).first()
    if not r or (u.role=="CLIENT" and r.client_id!=u.id): raise ResourceNotFoundError("Record not found")
    return success("Record found", record_dict(r))

@records_bp.get("/<int:record_pk>")
def get_record(record_pk):
    """Get one authorized record."""
    u=current_user(); r=find_record(record_pk)
    if u.role=="CLIENT" and r.client_id!=u.id: raise AuthorizationError("Access denied")
    return success("Record fetched", record_dict(r))

@records_bp.get("/<int:record_pk>/pdf")
def download_pdf(record_pk):
    """Generate and download PDF for a record."""

    u = current_user()

    r = find_record(record_pk)

    if u.role == "CLIENT" and r.client_id != u.id:
        raise AuthorizationError("Access denied")

    pdf = PDFService.generate_pdf(r)

    response = make_response(pdf)

    response.headers["Content-Type"] = "application/pdf"

    response.headers["Content-Disposition"] = (
        f'attachment; filename="{r.record_id}.pdf"'
    )

    return response

@records_bp.put("/<int:record_pk>")
def update_record(record_pk):
    """Update a record; locked records are admin-editable only."""
    u=current_user(); r=find_record(record_pk)
    if u.role=="CLIENT" and (r.client_id!=u.id or r.is_locked): raise AuthorizationError("Client cannot modify this locked record")
    data=validate_record(); payload=data.model_dump(mode="json"); old=record_dict(r)
    for k,v in payload.items(): setattr(r,k,v)
    r.updated_by=u.id; r.version+=1; r.input_json=payload
    r.extracted_json={**payload,"processed_by":"backend","version":r.version}
    audit(u.id,"UPDATE","main_table",r.record_id,old,payload)
    try: db.session.commit()
    except IntegrityError as exc: db.session.rollback(); raise DuplicateRecordError("Duplicate Record ID") from exc
    return success("Record updated",record_dict(r))

@records_bp.delete("/<int:record_pk>")
@roles_required("ADMIN")
def delete_record(record_pk):
    """Soft delete a record."""
    u=current_user(); r=find_record(record_pk); r.is_deleted=True; r.updated_by=u.id
    audit(u.id,"SOFT_DELETE","main_table",r.record_id,record_dict(r),{"is_deleted":True}); db.session.commit()
    return success("Record deleted")

def workflow(action):
    """Apply an admin workflow action."""
    u=current_user()
    try: body=ActionSchema.model_validate(request.get_json(silent=True) or {})
    except PydanticValidationError as exc: raise ValidationError("Validation Failed",pydantic_errors(exc))
    r=find_record(body.id); old=record_dict(r)
    if action=="LOCK": r.is_locked=True; r.locked_by=u.id
    elif action=="UNLOCK": r.is_locked=False; r.locked_by=None
    elif action=="APPROVE": r.status="APPROVED"; r.approved_by=u.id; r.approved_at=datetime.now(timezone.utc)
    elif action=="REJECT": r.status="REJECTED"; r.approved_by=None; r.approved_at=None
    audit(u.id,action,"main_table",r.record_id,old,record_dict(r)); db.session.commit()
    if action == "APPROVE":
        EmailService.send_approval_email(r)
    elif action == "REJECT":
        EmailService.send_rejection_email(r)
    return success(f"Record {action.lower()} successful",record_dict(r))

@records_bp.post("/lock")
@roles_required("ADMIN")
def lock(): return workflow("LOCK")
@records_bp.post("/unlock")
@roles_required("ADMIN")
def unlock(): return workflow("UNLOCK")
@records_bp.post("/approve")
@roles_required("ADMIN")
def approve(): return workflow("APPROVE")
@records_bp.post("/reject")
@roles_required("ADMIN")
def reject(): return workflow("REJECT")
