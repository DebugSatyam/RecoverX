from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Customer, Payment, RecoveryAttempt, AuditEvent
from .risk_engine import assess_payment_risk, calculate_revenue_at_risk
from .ai_agent import (
    create_recovery_context,
    run_groq_ai_agent
)
from .policy_engine import evaluate_policy
from .razorpay_service import razorpay_service  
from datetime import datetime

Base.metadata.create_all(bind=engine)

app = FastAPI(title="RecoverX API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RecoverX API"
    }


@app.post("/demo/recovery-case")
def create_demo_recovery_case(db: Session = Depends(get_db)):
    customer = (
        db.query(Customer)
        .filter(Customer.email == "rahul@example.com")
        .first()
    )

    if customer is None:
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
        payment_id=payment.payment_id,
        ai_probability=0.87,
        recommended_action="delayed_retry",
        policy_decision="APPROVE",
        execution_result="pending",
        recovered_amount=0.0,
        timestamp=datetime.now().isoformat()
    )

    db.add(recovery)
    db.commit()
    db.refresh(recovery)

    audit = AuditEvent(
        recovery_attempt_id=recovery.id,
        event_type="recovery_created",
        description="RecoverX approved a delayed retry for a historically reliable customer.",
        timestamp=datetime.now().isoformat()
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "customer_id": customer.id,
        "payment_id": payment.payment_id,
        "recovery_attempt_id": recovery.id,
        "audit_event_id": audit.id
    }

@app.get("/risk/payment/{payment_id}")
def assess_payment(payment_id: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(payment.Payment_id == payment_id).first()

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

    # ---------------------------------------------
    # 1. Create recovery context
    # ---------------------------------------------

    context = create_recovery_context(
        payment,
        customer
    )

    # ---------------------------------------------
    # 2. Ask AI for recommendation
    # ---------------------------------------------

    recommendation = run_groq_ai_agent(context)

    # ---------------------------------------------
    # 3. Deterministic policy validation
    # ---------------------------------------------

    policy_decision = evaluate_policy(
        payment,
        recommendation
    )

    # ---------------------------------------------
    # 4. Save recovery attempt
    # ---------------------------------------------

    recovery = RecoveryAttempt(
        payment_id=payment.id,

        # AI decision
        ai_probability=recommendation.recovery_probability,
        confidence  =recommendation.confidence,
        diagnosis=recommendation.diagnosis,
        explanation=recommendation.explanation,
        retry_after_hours=recommendation.retry_after_hours,
        recommended_action=recommendation.recommended_action,
        # Deterministic policy decision
        policy_decision=policy_decision.decision,
        # Execution outcome
        execution_result="pending",
        recovered_amount=0.0,
        timestamp=datetime.now().isoformat()
    )

    db.add(recovery)
    db.commit()
    db.refresh(recovery)

    # ---------------------------------------------
    # 5. Save audit event
    # ---------------------------------------------

    audit = AuditEvent(
    recovery_attempt_id=recovery.id,
    event_type="ai_decision",
    description=(
        f"AI diagnosis: {recommendation.diagnosis} "
        f"Recovery probability: "
        f"{recommendation.recovery_probability:.2f}. "
        f"Confidence: {recommendation.confidence:.2f}. "
        f"Recommended action: "
        f"{recommendation.recommended_action}. "
        f"Retry after: "
        f"{recommendation.retry_after_hours} hours. "
        f"Explanation: {recommendation.explanation}"
    ),
    timestamp=datetime.now().isoformat()
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)


    policy_audit = AuditEvent(
    recovery_attempt_id=recovery.id,
    event_type="policy_evaluated",
    description=(
        f"RecoverX policy decision: "
        f"{policy_decision.decision}. "
        f"{policy_decision.reason}"
    ),
    timestamp=datetime.now().isoformat()
)

    db.add(policy_audit)
    db.commit()
    db.refresh(policy_audit)

    # ---------------------------------------------
    # 6. Return complete decision
    # ---------------------------------------------

    return {
        "payment_id": payment.id,

        "context": context.model_dump(),

        "recommendation": recommendation.model_dump(),

        "policy": {
            "decision": policy_decision.decision,
            "allowed": policy_decision.allowed,
            "reason": policy_decision.reason
        },

        "recovery_attempt": {
            "id": recovery.id,
            "execution_result": recovery.execution_result,
            "recovered_amount": recovery.recovered_amount
        },

        "audits": [
    {
        "id": audit.id,
        "event_type": audit.event_type,
        "description": audit.description
    },
    {
        "id": policy_audit.id,
        "event_type": policy_audit.event_type,
        "description": policy_audit.description
    }
]
    }

@app.post("/recovery/execute/{recovery_id}")
def execute_recovery(
    recovery_id: int,
    db: Session = Depends(get_db)
):
    # ---------------------------------------------
    # 1. Find recovery attempt
    # ---------------------------------------------

    recovery = (
        db.query(RecoveryAttempt)
        .filter(RecoveryAttempt.id == recovery_id)
        .first()
    )

    if recovery is None:
        return {
            "error": "Recovery attempt not found"
        }

    # ---------------------------------------------
    # 2. Safety boundary
    # ---------------------------------------------

    if recovery.policy_decision != "APPROVE":
        return {
            "status": "blocked",
            "reason": (
                "Recovery execution is only allowed "
                "for APPROVE policy decisions."
            ),
            "recovery_attempt_id": recovery.id
        }

    # ---------------------------------------------
    # 2b. Prevent duplicate execution
    # ---------------------------------------------

    if recovery.execution_result != "pending":
        return {
            "status": "blocked",
            "reason": "Recovery attempt has already been executed.",
            "recovery_attempt_id": recovery.id,
            "execution_result": recovery.execution_result
        }

    # ---------------------------------------------
    # 3. Find payment
    # ---------------------------------------------

    payment = (
        db.query(Payment)
        .filter(Payment.id == recovery.payment_id)
        .first()
    )

    if payment is None:
        return {
            "error": "Payment not found"
        }

    # ---------------------------------------------
    # 4. Execute approved recovery
    # ---------------------------------------------

    result = razorpay_service.execute_recovery(
        payment,
        recovery.recommended_action
    )

    # ---------------------------------------------
    # 5. Save execution outcome
    # ---------------------------------------------

    recovery.execution_result = result["status"]
    recovery.recovered_amount = result["recovered_amount"]

    db.commit()
    db.refresh(recovery)

    # ---------------------------------------------
    # 6. Create audit event
    # ---------------------------------------------

    audit = AuditEvent(
        recovery_attempt_id=recovery.id,
        event_type="recovery_executed",
        description=(
            f"Recovery action '{recovery.recommended_action}' "
            f"executed with result '{result['status']}'. "
            f"Recovered amount: ₹{result['recovered_amount']:.2f}."
        ),
        timestamp=datetime.now().isoformat()
    )

    db.add(audit)
    db.commit()
    db.refresh(audit)

    # ---------------------------------------------
    # 7. Return execution result
    # ---------------------------------------------

    return {
        "status": result["status"],
        "message": result["message"],
        "payment_id": payment.id,
        "recovery_attempt_id": recovery.id,
        "executed_action": recovery.recommended_action,
        "recovered_amount": recovery.recovered_amount,
        "audit": {
            "id": audit.id,
            "event_type": audit.event_type,
            "description": audit.description
        }
    }

@app.get("/recovery/queue")
def recovery_queue(db: Session = Depends(get_db)):
    recoveries = (
        db.query(RecoveryAttempt)
        .order_by(RecoveryAttempt.id.desc())
        .all()
    )

    queue = []

    for recovery in recoveries:
        payment = (
            db.query(Payment)
            .filter(Payment.id == recovery.payment_id)
            .first()
        )

        if payment is None:
            continue

        customer = (
            db.query(Customer)
            .filter(Customer.id == payment.customer_id)
            .first()
        )

        queue.append({
            "recovery_id": recovery.id,
            "payment_id": payment.id,
            "customer": customer.name if customer else "Unknown",
            "amount": payment.amount,
            "reason": payment.failure_reason,
            "probability": recovery.ai_probability,
            "action": recovery.recommended_action,
            "status": (
                "Ready"
                if recovery.policy_decision == "APPROVE"
                else "Review"
            ),
            "policy_decision": recovery.policy_decision,
            "execution_result": recovery.execution_result,
        })

    return {
        "count": len(queue),
        "queue": queue
    }

@app.get("/audit/recovery/{recovery_id}")
def get_recovery_audit(
    recovery_id: int,
    db: Session = Depends(get_db)
):
    recovery = (
        db.query(RecoveryAttempt)
        .filter(RecoveryAttempt.id == recovery_id)
        .first()
    )

    if recovery is None:
        return {
            "error": "Recovery attempt not found"
        }

    events = (
        db.query(AuditEvent)
        .filter(
            AuditEvent.recovery_attempt_id == recovery_id
        )
        .order_by(AuditEvent.id.asc())
        .all()
    )

    return {
        "recovery_id": recovery_id,
        "count": len(events),
        "events": [
            {
                "id": event.id,
                "event_type": event.event_type,
                "description": event.description,
                "timestamp": event.timestamp
            }
            for event in events
        ]
    }