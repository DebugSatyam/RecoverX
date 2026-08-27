from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Customer, Payment, RecoveryAttempt, AuditEvent
from .risk_engine import assess_payment_risk, calculate_revenue_at_risk
from .ai_agent import (
    create_recovery_context,
    run_groq_ai_agent
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RecoverX API")


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RecoverX API"
    }


@app.post("/demo/recovery-case")
def create_demo_recovery_case(db: Session = Depends(get_db)):
    customer = Customer(
        name="Rahul Sharma",
        email="rahul@example.com",
        successful_payments=8,
        failed_payments=1,
        lifetime_value=39992.0,
        payment_reliability=0.89
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    payment = Payment(
        customer_id=customer.id,
        amount=4999.0,
        status="failed",
        failure_reason="insufficient_funds",
        attempt_count=1,
        timestamp="2026-08-25T10:00:00",
        razorpay_payment_id=None
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    recovery = RecoveryAttempt(
        payment_id=payment.id,
        ai_probability=0.87,
        recommended_action="delayed_retry",
        policy_decision="approved",
        execution_result="pending",
        recovered_amount=0.0,
        timestamp="2026-08-25T10:05:00"
    )

    db.add(recovery)
    db.commit()
    db.refresh(recovery)

    audit = AuditEvent(
        recovery_attempt_id=recovery.id,
        event_type="recovery_created",
        description="RecoverX approved a delayed retry for a historically reliable customer.",
        timestamp="2026-08-25T10:05:00"
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "customer_id": customer.id,
        "payment_id": payment.id,
        "recovery_attempt_id": recovery.id,
        "audit_event_id": audit.id
    }

@app.get("/risk/payment/{payment_id}")
def assess_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if payment is None:
        return {
            "error": "Payment not found"
        }

    customer = (
        db.query(Customer)
        .filter(Customer.id == payment.customer_id)
        .first()
    )

    if customer is None:
        return {
            "error": "Customer not found"
        }

    assessment = assess_payment_risk(payment, customer)

    return {
        "payment_id": payment.id,
        "customer_id": customer.id,
        "amount": payment.amount,
        "status": payment.status,
        "failure_reason": payment.failure_reason,
        "attempt_count": payment.attempt_count,
        "risk_level": assessment.risk_level,
        "recovery_probability": assessment.recovery_probability,
        "reasons": assessment.reasons
    }

@app.get("/risk/overview")
def risk_overview(db: Session = Depends(get_db)):
    payments = db.query(Payment).all()
    customers = db.query(Customer).all()

    result = calculate_revenue_at_risk(
        payments,
        customers
    )

    return result

@app.get("/ai/context/{payment_id}")
def get_ai_context(
    payment_id: int,
    db: Session = Depends(get_db)
):
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if payment is None:
        return {
            "error": "Payment not found"
        }

    customer = (
        db.query(Customer)
        .filter(Customer.id == payment.customer_id)
        .first()
    )

    if customer is None:
        return {
            "error": "Customer not found"
        }

    context = create_recovery_context(
        payment,
        customer
    )

    return context.model_dump()

@app.get("/ai/groq-recommendation/{payment_id}")
def get_groq_recommendation(
    payment_id: int,
    db: Session = Depends(get_db)
):
    payment = (
        db.query(Payment)
        .filter(Payment.id == payment_id)
        .first()
    )

    if payment is None:
        return {
            "error": "Payment not found"
        }

    customer = (
        db.query(Customer)
        .filter(Customer.id == payment.customer_id)
        .first()
    )

    if customer is None:
        return {
            "error": "Customer not found"
        }

    context = create_recovery_context(
        payment,
        customer
    )

    recommendation = run_groq_ai_agent(context)

    return {
        "payment_id": payment.id,
        "context": context.model_dump(),
        "recommendation": recommendation.model_dump()
    }