from dataclasses import dataclass


@dataclass
class EvaluationCase:
    name: str
    failure_reason: str
    amount: float
    attempt_count: int
    recovery_probability: float
    confidence: float
    recommended_action: str
    expected_policy_decision: str


EVALUATION_CASES = [
    EvaluationCase(
        name="reliable_insufficient_funds",
        failure_reason="insufficient_funds",
        amount=2499.0,
        attempt_count=1,
        recovery_probability=0.87,
        confidence=0.90,
        recommended_action="delayed_retry",
        expected_policy_decision="APPROVE",
    ),
    EvaluationCase(
        name="temporary_failure_low_confidence",
        failure_reason="temporary_failure",
        amount=1999.0,
        attempt_count=1,
        recovery_probability=0.75,
        confidence=0.45,
        recommended_action="delayed_retry",
        expected_policy_decision="ESCALATE",
    ),
    EvaluationCase(
        name="expired_card",
        failure_reason="card_expired",
        amount=2499.0,
        attempt_count=1,
        recovery_probability=0.30,
        confidence=0.90,
        recommended_action="customer_action_required",
        expected_policy_decision="STOP",
    ),
    EvaluationCase(
        name="retry_limit_reached",
        failure_reason="insufficient_funds",
        amount=4999.0,
        attempt_count=3,
        recovery_probability=0.90,
        confidence=0.95,
        recommended_action="delayed_retry",
        expected_policy_decision="STOP",
    ),
    EvaluationCase(
        name="high_value_payment",
        failure_reason="network_error",
        amount=15000.0,
        attempt_count=1,
        recovery_probability=0.90,
        confidence=0.95,
        recommended_action="delayed_retry",
        expected_policy_decision="ESCALATE",
    ),
    EvaluationCase(
        name="suspicious_payment",
        failure_reason="suspicious_activity",
        amount=2499.0,
        attempt_count=1,
        recovery_probability=0.90,
        confidence=0.95,
        recommended_action="delayed_retry",
        expected_policy_decision="STOP",
    ),
    EvaluationCase(
        name="unsupported_action",
        failure_reason="insufficient_funds",
        amount=2499.0,
        attempt_count=1,
        recovery_probability=0.90,
        confidence=0.95,
        recommended_action="customer_action_required",
        expected_policy_decision="STOP",
    ),
]

from types import SimpleNamespace

from .policy_engine import evaluate_policy


def evaluate_policy_cases():
    results = []

    for case in EVALUATION_CASES:
        payment = SimpleNamespace(
            amount=case.amount,
            attempt_count=case.attempt_count,
            failure_reason=case.failure_reason,
        )

        recommendation = SimpleNamespace(
            recovery_probability=case.recovery_probability,
            confidence=case.confidence,
            recommended_action=case.recommended_action,
        )

        decision = evaluate_policy(
            payment,
            recommendation,
        )

        results.append({
            "case": case.name,
            "expected": case.expected_policy_decision,
            "actual": decision.decision,
            "passed": decision.decision == case.expected_policy_decision,
            "reason": decision.reason,
        })

    return results


def calculate_policy_accuracy(results):
    if not results:
        return 0.0

    passed = sum(
        1
        for result in results
        if result["passed"]
    )

    return round(
        passed / len(results),
        4,
    )


def run_policy_evaluation():
    results = evaluate_policy_cases()

    return {
        "total_cases": len(results),
        "passed_cases": sum(
            1
            for result in results
            if result["passed"]
        ),
        "failed_cases": sum(
            1
            for result in results
            if not result["passed"]
        ),
        "policy_accuracy": calculate_policy_accuracy(results),
        "cases": results,
    }

def calculate_recovery_metrics(recoveries):
    total_recovery_cases = len(recoveries)

    successful_recoveries = sum(
        1
        for recovery in recoveries
        if recovery.execution_result == "success"
    )

    failed_recoveries = sum(
        1
        for recovery in recoveries
        if recovery.execution_result == "failed"
    )

    pending_recoveries = sum(
        1
        for recovery in recoveries
        if recovery.execution_result == "pending"
    )

    recovered_revenue = sum(
        recovery.recovered_amount or 0.0
        for recovery in recoveries
    )

    attempted_revenue = sum(
        recovery.recovered_amount or 0.0
        for recovery in recoveries
        if recovery.execution_result in {"success", "failed"}
    )

    recovery_rate = (
        successful_recoveries / total_recovery_cases
        if total_recovery_cases > 0
        else 0.0
    )

    return {
        "total_recovery_cases": total_recovery_cases,
        "successful_recoveries": successful_recoveries,
        "failed_recoveries": failed_recoveries,
        "pending_recoveries": pending_recoveries,
        "recovered_revenue": round(recovered_revenue, 2),
        "case_recovery_rate": round(recovery_rate, 4),
        "attempted_revenue": round(attempted_revenue, 2),
    }

def evaluate_recovery_database(db):
    from .models import RecoveryAttempt

    recoveries = (
        db.query(RecoveryAttempt)
        .all()
    )

    return calculate_recovery_metrics(recoveries)

def calculate_revenue_recovery_metrics(recoveries, payments):
    payment_map = {
        payment.id: payment
        for payment in payments
    }

    revenue_at_risk = 0.0
    recovered_revenue = 0.0

    for recovery in recoveries:
        payment = payment_map.get(recovery.payment_id)

        if payment is None:
            continue

        revenue_at_risk += payment.amount
        recovered_revenue += recovery.recovered_amount or 0.0

    recovery_rate = (
        recovered_revenue / revenue_at_risk
        if revenue_at_risk > 0
        else 0.0
    )

    return {
        "revenue_at_risk": round(revenue_at_risk, 2),
        "recovered_revenue": round(recovered_revenue, 2),
        "revenue_recovery_rate": round(recovery_rate, 4),
    }