import os
import base64
import resend

from services.pdf_service import PDFService


class EmailService:
    """Service for sending record notifications using Resend."""

    @staticmethod
    def _configure():
        api_key = os.getenv("RESEND_API_KEY")

        if not api_key:
            raise RuntimeError("RESEND_API_KEY is not configured")

        resend.api_key = api_key


    @staticmethod
    def send_approval_email(record):
        EmailService._configure()

        # Generate approved record PDF
        pdf_bytes = PDFService.generate_pdf(record)

        # Convert PDF bytes to Base64
        pdf_base64 = base64.b64encode(pdf_bytes).decode("utf-8")

        params = {
            "from": "Record Management System <onboarding@resend.dev>",
            "to": [record.email],
            "subject": f"Record {record.record_id} Approved",

            "html": f"""
                <h2>Record Approved</h2>

                <p>Hello {record.name},</p>

                <p>Your record has been approved successfully.</p>

                <p>
                    <strong>Record ID:</strong> {record.record_id}<br>
                    <strong>Status:</strong> APPROVED
                </p>

                <p>
                    Please find your approved record attached to this email.
                </p>

                <p>
                    Regards,<br>
                    Record Management System
                </p>
            """,

            "attachments": [
                {
                    "filename": f"{record.record_id}.pdf",
                    "content": pdf_base64
                }
            ]
        }

        return resend.Emails.send(params)


    @staticmethod
    def send_rejection_email(record):
        EmailService._configure()

        params = {
            "from": "Record Management System <onboarding@resend.dev>",
            "to": [record.email],
            "subject": f"Record {record.record_id} Rejected",

            "html": f"""
                <h2>Record Rejected</h2>

                <p>Hello {record.name},</p>

                <p>
                    Unfortunately, your record has been rejected.
                </p>

                <p>
                    <strong>Record ID:</strong> {record.record_id}<br>
                    <strong>Status:</strong> REJECTED
                </p>

                <p>
                    Regards,<br>
                    Record Management System
                </p>
            """
        }

        return resend.Emails.send(params)