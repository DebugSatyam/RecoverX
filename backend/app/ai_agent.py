import os

from dotenv import load_dotenv
from groq import Groq

from pydantic import BaseModel, Field
from typing import Literal


load_dotenv()

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

def run_groq_ai_agent(
    context: RecoveryContext,
) -> RecoveryRecommendation:

    prompt = f"""
You are the RecoverX AI revenue recovery agent.

Your job is to analyze a failed payment and recommend
the safest possible recovery action.

You are NOT allowed to execute payments.
You only provide a recommendation.

Payment context:
{context.model_dump_json(indent=2)}

Rules:
- Consider the deterministic risk assessment as an input.
- Do not invent customer information.
- Do not recommend retrying an expired card.
- Do not recommend automatic recovery if the retry limit
  has already been reached.
- Prefer the safest reasonable intervention.
- Return a structured recommendation.
"""

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a cautious AI revenue recovery "
                    "agent for RecoverX."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.2,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "recovery_recommendation",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "diagnosis": {
                            "type": "string"
                        },
                        "recovery_probability": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        },
                        "recommended_action": {
                            "type": "string",
                            "enum": [
                                "delayed_retry",
                                "immediate_retry",
                                "customer_action_required",
                                "no_action"
                            ]
                        },
                        "retry_after_hours": {
                            "type": [
                                "integer",
                                "null"
                            ],
                            "minimum": 0
                        },
                        "confidence": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1
                        },
                        "explanation": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "diagnosis",
                        "recovery_probability",
                        "recommended_action",
                        "retry_after_hours",
                        "confidence",
                        "explanation"
                    ],
                    "additionalProperties": False
                }
            }
        }
    )

    result = response.choices[0].message.content

    return RecoveryRecommendation.model_validate_json(result)

class RecoveryRecommendation(BaseModel):
    diagnosis: str

    recovery_probability: float = Field(
        ge=0.0,
        le=1.0
    )

    recommended_action: Literal[
        "delayed_retry",
        "immediate_retry",
        "customer_action_required",
        "no_action"
    ]

    retry_after_hours: int | None = Field(
        default=None,
        ge=0
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0
    )

    explanation: str

class RecoveryContext(BaseModel):
    payment_id: int
    amount: float
    failure_reason: str | None
    attempt_count: int

    customer_successful_payments: int
    customer_failed_payments: int
    customer_payment_reliability: float
    customer_lifetime_value: float

    risk_level: str
    risk_probability: float
    risk_reasons: list[str]

def build_recovery_context(payment, customer, risk_assessment):
    return RecoveryContext(
        payment_id=payment.id,
        amount=payment.amount,
        failure_reason=payment.failure_reason,
        attempt_count=payment.attempt_count,
        customer_successful_payments=customer.successful_payments,
        customer_failed_payments=customer.failed_payments,
        customer_payment_reliability=customer.payment_reliability,
        customer_lifetime_value=customer.lifetime_value,
        risk_level=risk_assessment.risk_level,
        risk_probability=risk_assessment.recovery_probability,
        risk_reasons=risk_assessment.reasons,
    )

def create_recovery_context(payment, customer):
    from .risk_engine import assess_payment_risk

    risk_assessment = assess_payment_risk(
        payment,
        customer
    )

    return build_recovery_context(
        payment,
        customer,
        risk_assessment
    )