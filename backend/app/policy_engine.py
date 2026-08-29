from dataclasses import dataclass


# Policy configuration
MAX_RETRY_ATTEMPTS = 3

# Prototype thresholds.
# These can be changed later without modifying the policy logic.
MIN_RECOVERY_PROBABILITY = 0.70
HIGH_VALUE_THRESHOLD = 10000.0


@dataclass
class PolicyDecision:
    decision: str
    allowed: bool
    reason: str


def evaluate_policy(
    payment,
    recommendation
) -> PolicyDecision:

    # --------------------------------------------------
    # STOP RULES
    # --------------------------------------------------

    # Rule 1: Retry limit reached
    if payment.attempt_count >= MAX_RETRY_ATTEMPTS:
        return PolicyDecision(
            decision="STOP",
            allowed=False,
            reason="Retry limit has been reached."
        )

    # Rule 2: Suspicious / fraud-related payment
    failure_reason = (payment.failure_reason or "").lower()

    suspicious_reasons = [
        "fraud",
        "fraudulent",
        "suspicious",
        "chargeback"
    ]

    if any(reason in failure_reason for reason in suspicious_reasons):
        return PolicyDecision(
            decision="STOP",
            allowed=False,
            reason="Payment appears suspicious or fraud-related."
        )

    # --------------------------------------------------
    # ESCALATION RULES
    # --------------------------------------------------

    # Rule 3: High-value payment
    if payment.amount > HIGH_VALUE_THRESHOLD:
        return PolicyDecision(
            decision="ESCALATE",
            allowed=False,
            reason="Payment amount exceeds the automatic recovery threshold."
        )

    # Rule 4: Low confidence but non-zero recovery chance
    if (
        recommendation.recovery_probability > 0
        and recommendation.confidence < 0.60
    ):
        return PolicyDecision(
            decision="ESCALATE",
            allowed=False,
            reason="AI confidence is low despite a non-zero recovery probability."
        )

    # --------------------------------------------------
    # APPROVAL RULES
    # --------------------------------------------------

    # Rule 5: Recovery probability must be high enough
    if recommendation.recovery_probability < MIN_RECOVERY_PROBABILITY:
        return PolicyDecision(
            decision="STOP",
            allowed=False,
            reason="Recovery probability is below the automatic recovery threshold."
        )

    # Rule 6: Only supported recovery actions can be automated
    supported_actions = {
        "delayed_retry",
        "immediate_retry"
    }

    if recommendation.recommended_action not in supported_actions:
        return PolicyDecision(
            decision="STOP",
            allowed=False,
            reason="Recommended action is not supported for automatic recovery."
        )

    # --------------------------------------------------
    # APPROVE
    # --------------------------------------------------

    return PolicyDecision(
        decision="APPROVE",
        allowed=True,
        reason=(
            "Recovery probability is above the required threshold, "
            "retry limit has not been exceeded, and the recommended "
            "action is supported."
        )
    )