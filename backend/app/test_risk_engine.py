from types import SimpleNamespace

from risk_engine import assess_payment_risk


customer = SimpleNamespace(
    payment_reliability=0.89
)

payment = SimpleNamespace(
    amount=4999.0,
    failure_reason="insufficient_funds",
    attempt_count=1
)


result = assess_payment_risk(payment, customer)

print("Risk Level:", result.risk_level)
print("Recovery Probability:", result.recovery_probability)
print("Reasons:")

for reason in result.reasons:
    print("-", reason)