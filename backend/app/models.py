from sqlalchemy import Column, Integer, String, Float
from .database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)

    successful_payments = Column(Integer, default=0)
    failed_payments = Column(Integer, default=0)

    lifetime_value = Column(Float, default=0.0)
    payment_reliability = Column(Float, default=0.0)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(Integer, nullable=False, index=True)

    amount = Column(Float, nullable=False)

    status = Column(String, nullable=False)

    failure_reason = Column(String, nullable=True)

    attempt_count = Column(Integer, default=0)

    timestamp = Column(String, nullable=False)

    razorpay_payment_id = Column(String, nullable=True, unique=True)

class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id = Column(Integer, primary_key=True, index=True)

    payment_id = Column(Integer, nullable=False, index=True)

    # AI decision
    ai_probability = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    diagnosis = Column(String, nullable=True)
    explanation = Column(String, nullable=True)
    recommended_action = Column(String, nullable=True)
    retry_after_hours = Column(Integer, nullable=True)

    # Deterministic policy decision
    policy_decision = Column(String, nullable=True)

    # Execution outcome
    execution_result = Column(String, nullable=True)
    recovered_amount = Column(Float, default=0.0)

    timestamp = Column(String, nullable=False)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, index=True)

    recovery_attempt_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    event_type = Column(String, nullable=False)

    description = Column(String, nullable=False)

    timestamp = Column(String, nullable=False)