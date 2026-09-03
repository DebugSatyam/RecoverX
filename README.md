# RecoverX

RecoverX is an AI revenue recovery agent that identifies at-risk failed payments, recommends a safe recovery action, lets deterministic policy rules approve or block it, and measures the resulting revenue.

## Problem

Failed payments are not always lost revenue. Temporary failures, insufficient funds, and network issues can often be recovered, but retries need customer context, timing, and strict safety controls.

## Solution

RecoverX detects failed payments, analyzes risk, asks an AI agent for a structured diagnosis and recommendation, validates that recommendation with deterministic policy rules, executes only approved actions through the local Razorpay Test Mode adapter, records the outcome, and reports recovered revenue.

## Architecture

- **Next.js**: dark data-first dashboard for risk, recovery cases, AI decisions, audit events, and evaluation evidence.
- **FastAPI**: API and workflow orchestration.
- **Risk engine**: deterministic payment and customer risk assessment.
- **AI agent**: Groq structured recommendation containing diagnosis, probability, confidence, action, and explanation.
- **Experience memory**: V1 currently uses persisted customer payment history and recovery-attempt history as context; a separate learned model is not claimed.
- **Policy engine**: deterministic APPROVE, ESCALATE, or STOP safety boundary.
- **Razorpay Test Mode adapter**: local prototype execution adapter; it does not perform a production payment retry.
- **SQLite/SQLAlchemy**: customers, payments, recovery attempts, and audit events.

## Data Intelligence

The **Data / Upload** workspace accepts CSV and XLSX files up to 10 MB. Files are parsed in the browser and are not uploaded to the backend or an external AI provider. RecoverX reports detected columns, row counts, malformed values, and missing recommended fields without silently dropping rows.

Ask Your Data supports deterministic questions about total, successful, failed, and at-risk revenue; failed-payment counts; average amounts; failure-reason revenue; and top customers by failed revenue. Each answer shows the operation and number of rows used. Unsupported questions or missing columns return a clear limitation instead of an invented value.

## AI

AI receives payment amount, failure state, attempt count, customer history, reliability, lifetime value, and deterministic risk context. It returns validated structured data. AI proposes; it cannot execute payments or bypass policy rules.

## Safety

The policy engine stops payments that are not failed, have reached three attempts, are suspicious or fraud-related, are opted out, or have unsupported actions. High-value payments and low-confidence non-zero opportunities escalate. The execution endpoint independently checks approval, pending state, and payment status.

## Recovery Flow

**Detect -> Diagnose -> Decide -> Gate -> Act -> Measure -> Learn**

The recovery queue preserves historical attempts. `count` is the historical row count; `active_count` is the number of distinct payments with pending APPROVE or ESCALATE work. Successful, failed, and blocked attempts remain visible for auditability.

## Evaluation

`/evaluation/metrics` runs seven deterministic policy cases covering approval, escalation, retry limits, suspicious payments, expired cards, and unsupported actions. It also reports database-backed attempt and revenue metrics. Revenue at risk and recovered revenue are deduplicated by payment; only successful executions count as recovered. This is policy regression evidence, not a claim of model accuracy or a held-out ML evaluation.

## API

- `GET /health`
- `POST /demo/recovery-case`
- `GET /risk/payment/{payment_id}`
- `GET /risk/overview`
- `GET /ai/context/{payment_id}`
- `GET /ai/groq-recommendation/{payment_id}`
- `GET /recovery/queue`
- `POST /recovery/execute/{recovery_id}`
- `GET /audit/recovery/{recovery_id}`
- `GET /evaluation/metrics`

Data upload and questions are intentionally client-side and do not add a server file-storage endpoint.

## Setup

Backend (PowerShell):

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend (a second terminal):

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`. The API runs at `http://127.0.0.1:8000`.

## Environment Variables

Create `backend/.env` or a repository `.env` from `.env.example`:

- `GROQ_API_KEY`: required for live AI recommendations.
- `RAZORPAY_KEY_ID`: Razorpay Test Mode key ID used by the client adapter.
- `RAZORPAY_KEY_SECRET`: Razorpay Test Mode secret.

Never commit `.env` files or credentials. The frontend only calls the backend and does not contain payment credentials.

## Demo

1. Start the backend and frontend.
2. Open the dashboard and note Revenue at Risk and Active Actions.
3. Open Recovery and select a `Ready` case.
4. Review risk context, AI diagnosis, probability, recommendation, and policy decision.
5. Execute the approved recovery.
6. Confirm the case becomes Completed, recovered revenue changes, and the audit timeline records execution.
7. Inspect `/evaluation/metrics` or the policy evaluation panel.
8. Select a `Blocked` or `Review` case to demonstrate that policy prevents direct execution.

## Limitations

The current Razorpay service models a successful or failed Test Mode retry locally and does not call a live payment API. Experience memory is persisted history/context rather than vector retrieval or model retraining. Uploaded datasets are held in the current browser session and are not persisted between reloads. The policy evaluation set is deterministic and small, not a held-out production dataset. Authentication and authorization for multi-user deployment are outside this buildathon prototype.

## Future Work

Add authenticated operator roles, an idempotency key and transactional claim for concurrent execution, provider-backed Test Mode retries, richer persisted experience retrieval, and a genuine held-out evaluation dataset.
