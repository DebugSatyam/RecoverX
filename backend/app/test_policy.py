from types import SimpleNamespace

from .policy_engine import evaluate_policy


def test_approve_case():
    payment = SimpleNamespace(
        amount=4999.0,
        attempt_count=1,
        failure_reason="insufficient_funds"
    )

    recommendation = SimpleNamespace(
        recovery_probability=0.87,
        confidence=0.91,
        recommended_action="delayed_retry"
    )

    decision = evaluate_policy(
        payment,
        recommendation
    )

    assert decision.decision == "APPROVE"
    assert decision.allowed is True


def test_stop_after_retry_limit():
    payment = SimpleNamespace(
        amount=4999.0,
        attempt_count=3,
        failure_reason="insufficient_funds"
    )

    recommendation = SimpleNamespace(
        recovery_probability=0.95,
        confidence=0.95,
        recommended_action="delayed_retry"
    )

    decision = evaluate_policy(
        payment,
        recommendation
    )

    assert decision.decision == "STOP"
    assert decision.allowed is False


def test_escalate_high_value_payment():
    payment = SimpleNamespace(
        amount=15000.0,
        attempt_count=1,
        failure_reason="insufficient_funds"
    )

    recommendation = SimpleNamespace(
        recovery_probability=0.90,
        confidence=0.90,
        recommended_action="delayed_retry"
    )

    decision = evaluate_policy(
        payment,
        recommendation
    )

    assert decision.decision == "ESCALATE"
    assert decision.allowed is False


def test_stop_unsupported_action():
    payment = SimpleNamespace(
        amount=4999.0,
        attempt_count=1,
        failure_reason="insufficient_funds"
    )

    recommendation = SimpleNamespace(
        recovery_probability=0.90,
        confidence=0.90,
        recommended_action="customer_action_required"
    )

    decision = evaluate_policy(
        payment,
        recommendation
    )

    assert decision.decision == "STOP"
    assert decision.allowed is False