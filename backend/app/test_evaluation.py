from .evaluation import run_policy_evaluation
import pytest
from fastapi.testclient import TestClient
from .main import app

def test_policy_evaluation():
    evaluation = run_policy_evaluation()

    assert evaluation["total_cases"] == 7
    assert evaluation["passed_cases"] == 7
    assert evaluation["failed_cases"] == 0
    assert evaluation["policy_accuracy"] == 1.0

from types import SimpleNamespace

from .evaluation import calculate_recovery_metrics
from .evaluation import calculate_revenue_recovery_metrics


def test_recovery_metrics():
    recoveries = [
        SimpleNamespace(
            execution_result="success",
            recovered_amount=1000.0,
        ),
        SimpleNamespace(
            execution_result="success",
            recovered_amount=500.0,
        ),
        SimpleNamespace(
            execution_result="failed",
            recovered_amount=0.0,
        ),
        SimpleNamespace(
            execution_result="pending",
            recovered_amount=0.0,
        ),
    ]

    metrics = calculate_recovery_metrics(recoveries)

    assert metrics["total_recovery_cases"] == 4
    assert metrics["successful_recoveries"] == 2
    assert metrics["failed_recoveries"] == 1
    assert metrics["pending_recoveries"] == 1
    assert metrics["recovered_revenue"] == 1500.0
    assert metrics["case_recovery_rate"] == 0.5


def test_revenue_recovery_metrics():
    payments = [
        SimpleNamespace(
            id=1,
            amount=2000.0,
        ),
        SimpleNamespace(
            id=2,
            amount=3000.0,
        ),
    ]

    recoveries = [
        SimpleNamespace(
            payment_id=1,
            recovered_amount=2000.0,
        ),
        SimpleNamespace(
            payment_id=2,
            recovered_amount=1000.0,
        ),
    ]

    metrics = calculate_revenue_recovery_metrics(
        recoveries,
        payments,
    )

    assert metrics["revenue_at_risk"] == 5000.0
    assert metrics["recovered_revenue"] == 3000.0
    assert metrics["revenue_recovery_rate"] == 0.6


def test_recovery_metrics_with_no_recoveries():
    metrics = calculate_recovery_metrics([])

    assert metrics["total_recovery_cases"] == 0
    assert metrics["successful_recoveries"] == 0
    assert metrics["failed_recoveries"] == 0
    assert metrics["pending_recoveries"] == 0
    assert metrics["recovered_revenue"] == 0.0
    assert metrics["case_recovery_rate"] == 0.0
    assert metrics["attempted_revenue"] == 0.0


def test_revenue_recovery_metrics_with_missing_payment():
    payments = [
        SimpleNamespace(id=1, amount=2000.0),
    ]

    recoveries = [
        SimpleNamespace(payment_id=1, recovered_amount=1000.0),
        SimpleNamespace(payment_id=999, recovered_amount=500.0),
    ]

    metrics = calculate_revenue_recovery_metrics(recoveries, payments)

    assert metrics["revenue_at_risk"] == 2000.0
    assert metrics["recovered_revenue"] == 1000.0
    assert metrics["revenue_recovery_rate"] == 0.5

def test_recovery_metrics_do_not_count_failed_or_pending_as_recovered():
    recoveries = [
        SimpleNamespace(execution_result="success", recovered_amount=2000.0),
        SimpleNamespace(execution_result="failed", recovered_amount=0.0),
        SimpleNamespace(execution_result="pending", recovered_amount=0.0),
    ]

    metrics = calculate_recovery_metrics(recoveries)

    assert metrics["total_recovery_cases"] == 3
    assert metrics["successful_recoveries"] == 1
    assert metrics["failed_recoveries"] == 1
    assert metrics["pending_recoveries"] == 1
    assert metrics["recovered_revenue"] == 2000.0
    assert metrics["case_recovery_rate"] == pytest.approx(1 / 3, abs=0.0001)
    assert metrics["attempted_revenue"] == 2000.0

def test_evaluation_metrics_endpoint():
    client = TestClient(app)

    response = client.get("/evaluation/metrics")

    assert response.status_code == 200

    data = response.json()

    assert "policy_evaluation" in data
    assert "recovery_metrics" in data
    assert "revenue_metrics" in data

    assert data["policy_evaluation"]["policy_accuracy"] == 1.0
    assert data["policy_evaluation"]["passed_cases"] == 7
    assert data["policy_evaluation"]["failed_cases"] == 0

    assert "case_recovery_rate" in data["recovery_metrics"]
    assert "revenue_recovery_rate" in data["revenue_metrics"]