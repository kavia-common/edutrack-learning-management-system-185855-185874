from __future__ import annotations

import io
from datetime import datetime
from typing import Optional, Tuple

import stripe
from flask import current_app
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from . import db
from .models import User, Role, Enrollment, Payment, Notification, Quiz
from .security import hash_password, verify_password


# PUBLIC_INTERFACE
def init_stripe_from_config():
    """Initialize Stripe library from app config. Returns None."""
    secret = current_app.config.get("STRIPE_SECRET_KEY", "")
    if secret:
        stripe.api_key = secret


# PUBLIC_INTERFACE
def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user by email and password."""
    user = User.query.filter_by(email=email).first()
    if user and verify_password(password, user.password_hash):
        return user
    return None


# PUBLIC_INTERFACE
def create_user(email: str, password: str, full_name: str, role_name: str = "student") -> Tuple[Optional[User], Optional[str]]:
    """Create a new user with role; returns (user, error)."""
    if User.query.filter_by(email=email).first():
        return None, "Email already in use"
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        role = Role(name=role_name)
        db.session.add(role)
        db.session.flush()
    user = User(email=email, password_hash=hash_password(password), full_name=full_name, role=role)
    db.session.add(user)
    db.session.commit()
    return user, None


# PUBLIC_INTERFACE
def enroll_user_in_course(user_id: int, course_id: int) -> Tuple[Optional[Enrollment], Optional[str]]:
    """Enroll a user into a course if not already enrolled."""
    existing = Enrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
    if existing:
        return existing, None
    enrollment = Enrollment(user_id=user_id, course_id=course_id, status="active")
    db.session.add(enrollment)
    db.session.commit()
    return enrollment, None


# PUBLIC_INTERFACE
def create_payment_intent(user_id: int, course_id: int, amount_cents: int, currency: str = "usd") -> Tuple[Optional[str], Optional[str]]:
    """Create a Stripe PaymentIntent and persist Payment record. Returns (client_secret, error)."""
    init_stripe_from_config()
    if not stripe.api_key:
        return None, "Stripe not configured"
    payment = Payment(user_id=user_id, course_id=course_id, amount_cents=amount_cents, currency=currency, status="created")
    db.session.add(payment)
    db.session.flush()
    intent = stripe.PaymentIntent.create(
        amount=amount_cents,
        currency=currency,
        metadata={"payment_id": str(payment.id), "user_id": str(user_id), "course_id": str(course_id)},
        automatic_payment_methods={"enabled": True},
    )
    payment.stripe_payment_intent_id = intent["id"]
    db.session.commit()
    return intent["client_secret"], None


# PUBLIC_INTERFACE
def mark_payment_succeeded(payment_intent_id: str) -> Optional[str]:
    """Mark payment as succeeded and return error if any."""
    payment = Payment.query.filter_by(stripe_payment_intent_id=payment_intent_id).first()
    if not payment:
        return "Payment not found"
    payment.status = "succeeded"
    db.session.commit()
    # Auto-enroll on success
    enroll_user_in_course(payment.user_id, payment.course_id)
    return None


# PUBLIC_INTERFACE
def generate_certificate_pdf_bytes(student_name: str, course_title: str, issuer: str) -> bytes:
    """Generate a simple Certificate PDF and return raw bytes."""
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawCentredString(width / 2, height - 150, "Certificate of Completion")
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 200, "This certifies that")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 230, student_name)
    pdf.setFont("Helvetica", 14)
    pdf.drawCentredString(width / 2, height - 260, "has successfully completed the course")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, height - 290, course_title)
    pdf.setFont("Helvetica", 12)
    pdf.drawCentredString(width / 2, height - 330, f"Issued by {issuer} on {datetime.utcnow().strftime('%Y-%m-%d')}")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()


# PUBLIC_INTERFACE
def record_notification(user_id: int, message: str) -> Notification:
    """Create and persist a notification."""
    notif = Notification(user_id=user_id, message=message)
    db.session.add(notif)
    db.session.commit()
    return notif


# PUBLIC_INTERFACE
def grade_quiz(quiz: Quiz, answers: dict[int, int]) -> int:
    """
    Grade a quiz based on mapping of question_id -> selected_option_id.
    Returns numeric score as percentage integer.
    """
    if not quiz.questions:
        return 100
    total = len(quiz.questions)
    correct = 0
    for q in quiz.questions:
        selected = answers.get(q.id)
        if selected and q.correct_option_id == selected:
            correct += 1
    return int((correct / total) * 100)
