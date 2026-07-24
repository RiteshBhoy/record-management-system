import os

from flask import current_app, render_template
from weasyprint import HTML

from extensions import db
from models import MainTable, User


class PDFService:
    """Service responsible for preparing and generating PDFs."""

    @staticmethod
    def get_user_name(user_id):
        if not user_id:
            return "-"

        # SQLAlchemy 2.x style
        user = db.session.get(User, user_id)

        return user.full_name if user else "-"

    @staticmethod
    def mask_aadhaar(aadhaar):
        if not aadhaar:
            return "-"
        return "XXXXXXXX" + aadhaar[-4:]

    @staticmethod
    def mask_pan(pan):
        if not pan:
            return "-"
        return pan[:5] + "****" + pan[-1]

    @staticmethod
    def build_record_context(record: MainTable):

        return {

            "record_id": record.record_id,

            "status": record.status,

            "version": record.version,

            "personal": {
                "name": record.name,
                "age": record.age,
                "gender": record.sex,
                "blood_group": record.blood_group or "-",
                "nationality": record.nationality,
                "marital_status": record.marital_status or "-"
            },

            "contact": {
                "email": record.email,
                "phone": record.phone,
                "address": record.address,
                "city": record.city,
                "state": record.state,
                "country": record.country
            },

            "professional": {
                "occupation": record.occupation,
                "fees": record.fees
            },

            "identity": {
                "aadhaar": PDFService.mask_aadhaar(record.aadhaar),
                "pan": PDFService.mask_pan(record.pan)
            },

            "workflow": {

                "status": record.status,

                "validation_status": record.validation_status,

                "created_by": PDFService.get_user_name(record.created_by),

                "updated_by": PDFService.get_user_name(record.updated_by),

                "approved_by": PDFService.get_user_name(record.approved_by),

                "created_at": record.created_at.strftime("%d-%b-%Y %I:%M %p"),

                "updated_at": record.updated_at.strftime("%d-%b-%Y %I:%M %p"),

                "approved_at": (
                    record.approved_at.strftime("%d-%b-%Y %I:%M %p")
                    if record.approved_at else "-"
                )
            },

            "remarks": record.remarks or "-"
        }

    @staticmethod
    def generate_pdf(record: MainTable):
        print("Root Path:", current_app.root_path)
        print("Static Folder:", current_app.static_folder)

        context = PDFService.build_record_context(record)

        logo_path = os.path.join(
            current_app.root_path,
            "static",
            "images",
            "logo.avif"
        )
        print("Logo Path:", logo_path)
        print("Logo Exists:", os.path.exists(logo_path))
        
        css_path = os.path.join(
            current_app.root_path,
            "static",
            "pdf",
            "style.css"
        )

        print("CSS Path:", css_path)
        print("CSS Exists:", os.path.exists(css_path))

        html = render_template(
            "pdf/record_summary.html",
            data=context,
            logo_path=logo_path,
            css_path=css_path
        )

        pdf = HTML(
            string=html,
            base_url=current_app.root_path
        ).write_pdf()

        return pdf