from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Customer, Payment, RecoveryAttempt, AuditEvent


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