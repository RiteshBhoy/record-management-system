from flask_mail import Message
from extensions import mail
from services.pdf_service import PDFService


class EmailService:

    @staticmethod
    def send_approval_email(record):

        msg = Message(
            subject=f"Record {record.record_id} Approved",
            recipients=[record.email]
        )

        msg.body = f"""
Hello {record.name},

Congratulations!

Your record has been approved successfully.

Record ID : {record.record_id}

Please find your approved record attached.

Regards,
Record Management System
"""

        # Generate PDF
        pdf_bytes = PDFService.generate_pdf(record)

        # Attach PDF
        msg.attach(
            filename=f"{record.record_id}.pdf",
            content_type="application/pdf",
            data=pdf_bytes,
        )

        mail.send(msg)

    @staticmethod
    def send_rejection_email(record):

        msg = Message(
            subject=f"Record {record.record_id} Rejected",
            recipients=[record.email]
        )

        msg.body = f"""
Hello {record.name},

Unfortunately your record has been rejected.

Record ID : {record.record_id}

Regards,
Record Management System
"""

        mail.send(msg)