import json
from flask import request, current_app
from flask_smorest import Blueprint
from flask.views import MethodView
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..models import Course
from ..services import create_payment_intent, mark_payment_succeeded, init_stripe_from_config

import stripe

blp = Blueprint(
    "Payments",
    "payments",
    url_prefix="/api/payments",
    description="Stripe payments via PaymentIntents and webhook",
)


@blp.route("/intent/<int:course_id>")
class CreateIntent(MethodView):
    """
    PUBLIC_INTERFACE
    Create a Stripe PaymentIntent for purchasing a course.
    """
    @jwt_required()
    def post(self, course_id: int):
        course = Course.query.get_or_404(course_id)
        ident = get_jwt_identity()
        client_secret, err = create_payment_intent(ident.get("id"), course_id, course.price_cents or 0, "usd")
        if err:
            return {"message": err}, 400
        return {"client_secret": client_secret}


@blp.route("/webhook")
class StripeWebhook(MethodView):
    """
    PUBLIC_INTERFACE
    Stripe webhook to handle payment events.
    """
    def post(self):
        init_stripe_from_config()
        payload = request.data
        sig_header = request.headers.get("Stripe-Signature", "")
        endpoint_secret = current_app.config.get("STRIPE_WEBHOOK_SECRET", "")
        try:
            if endpoint_secret:
                event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
            else:
                event = json.loads(payload.decode("utf-8"))
        except Exception as e:
            return {"message": "Invalid payload", "error": str(e)}, 400

        event_type = event.get("type")
        if event_type == "payment_intent.succeeded":
            intent = event["data"]["object"]
            mark_payment_succeeded(intent.get("id"))

        return {"received": True}, 200
