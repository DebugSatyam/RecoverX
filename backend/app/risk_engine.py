from dataclasses import dataclass


@dataclass
class RiskAssessment:
    risk_level: str
    recovery_probability: float
    reasons: list[str]


def assess_payment_risk(payment, customer) -> RiskAssessment:
    """
    Deterministic baseline risk assessment.

    This is NOT the AI agent.
    It creates structured risk context that can later
    be passed to the AI agent.
    """

    if payment.status != "failed":
        return RiskAssessment(
            risk_level="not_at_risk",
            recovery_probability=0.0,
            reasons=[
                "Payment is not failed and is not a recovery candidate."
            ],
        )

    score = 0.50
    reasons = []

    # Customer reliability
    if customer.payment_reliability >= 0.85:
        score += 0.20
        reasons.append("Customer has strong payment reliability.")
    elif customer.payment_reliability >= 0.60:
        score += 0.05
        reasons.append("Customer has moderate payment reliability.")
    else:
        score -= 0.20
        reasons.append("Customer has low payment reliability.")

    # Failure reason
        # Failure reason
    if payment.failure_reason == "insufficient_funds":
        score += 0.15
        reasons.append(
            "Insufficient funds may be recoverable after a delay."
        )

    elif payment.failure_reason == "network_error":
        score += 0.10
        reasons.append(
            "Network-related failure may be temporary."
        )

    elif payment.failure_reason == "temporary_failure":
        score += 0.10
        reasons.append(
            "Temporary failure may resolve without customer intervention."
        )

    elif payment.failure_reason == "authentication_failed":
        score -= 0.10
        reasons.append(
            "Authentication failure may require customer intervention."
        )

    elif payment.failure_reason == "card_expired":
        score -= 0.25
        reasons.append(
            "Expired card generally requires the customer to update payment details."
        )

    else:
        reasons.append(
            "Failure reason has uncertain recovery behavior."
        )

    # Attempt count
    if payment.attempt_count >= 3:
        score -= 0.40
        reasons.append("Retry limit has been reached.")

    elif payment.attempt_count == 2:
        score -= 0.10
        reasons.append("Payment has already been attempted twice.")

    else:
        reasons.append("Retry limit has not been reached.")

    # Clamp probability
    probability = max(0.0, min(score, 0.95))

    # Risk classification
    if probability >= 0.70:
        risk_level = "high_recovery"
    elif probability >= 0.40:
        risk_level = "medium_recovery"
    else:
        risk_level = "low_recovery"

    return RiskAssessment(
        risk_level=risk_level,
        recovery_probability=round(probability, 2),
        reasons=reasons,
    )

def calculate_revenue_at_risk(payments, customers):
    """
    Calculate actionable revenue at risk and expected recoverable revenue.
    """

    customer_map = {
        customer.id: customer
        for customer in customers
    }

    revenue_at_risk = 0.0
    expected_recoverable_revenue = 0.0

    high_recovery_cases = 0
    medium_recovery_cases = 0
    low_recovery_cases = 0

    for payment in payments:
        customer = customer_map.get(payment.customer_id)

        if customer is None:
            continue

        assessment = assess_payment_risk(payment, customer)

        if assessment.risk_level == "high_recovery":
            revenue_at_risk += payment.amount
            expected_recoverable_revenue += (
                payment.amount * assessment.recovery_probability
            )
            high_recovery_cases += 1

        elif assessment.risk_level == "medium_recovery":
            revenue_at_risk += payment.amount
            expected_recoverable_revenue += (
                payment.amount * assessment.recovery_probability
            )
            medium_recovery_cases += 1

        elif assessment.risk_level == "low_recovery":
            low_recovery_cases += 1

    return {
        "revenue_at_risk": round(revenue_at_risk, 2),
        "expected_recoverable_revenue": round(
            expected_recoverable_revenue, 2
        ),
        "high_recovery_cases": high_recovery_cases,
        "medium_recovery_cases": medium_recovery_cases,
        "low_recovery_cases": low_recovery_cases,
    }