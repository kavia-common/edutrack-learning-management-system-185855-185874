from flask import send_file, current_app
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity
import io

from ..models import Course, Enrollment, User
from ..services import generate_certificate_pdf_bytes

blp = Blueprint(
    "Certificates",
    "certificates",
    url_prefix="/api/certificates",
    description="Certificate generation endpoints",
)


@blp.route("/course/<int:course_id>")
class CourseCertificate(MethodView):
    """
    PUBLIC_INTERFACE
    Generate a certificate PDF for a completed course.
    """
    @jwt_required()
    def get(self, course_id: int):
        ident = get_jwt_identity()
        enrollment = Enrollment.query.filter_by(user_id=ident.get("id"), course_id=course_id, status="completed").first()
        if not enrollment:
            return {"message": "Certificate available only after course completion"}, 400
        user = User.query.get(ident.get("id"))
        course = Course.query.get_or_404(course_id)
        issuer = current_app.config.get("CERTIFICATE_ISSUER", "EduTrack")
        pdf_bytes = generate_certificate_pdf_bytes(user.full_name, course.title, issuer)
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"certificate_{course_id}_{user.id}.pdf",
        )
