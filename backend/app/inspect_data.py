from sqlalchemy import func

from .database import SessionLocal
from .models import Customer, Payment


def inspect_dataset():
    db = SessionLocal()

    try:
        total_customers = (
            db.query(Customer)
            .filter(Customer.email != "dataset-marker@recoverx.local")
            .count()
        )

        total_payments = db.query(Payment).count()

        successful_payments = (
            db.query(Payment)
            .filter(Payment.status == "success")
            .count()
        )

        failed_payments = (
            db.query(Payment)
            .filter(Payment.status == "failed")
            .count()
        )

        print("\n===== RECOVERX DATASET =====")
        print(f"Customers: {total_customers}")
        print(f"Payments: {total_payments}")
        print(f"Successful payments: {successful_payments}")
        print(f"Failed payments: {failed_payments}")

        print("\n===== FAILURE REASONS =====")

        failure_reasons = (
            db.query(
                Payment.failure_reason,
                func.count(Payment.id)
            )
            .filter(Payment.status == "failed")
            .group_by(Payment.failure_reason)
            .all()
        )

        for reason, count in failure_reasons:
            print(f"{reason}: {count}")

        print("============================\n")

    finally:
        db.close()


if __name__ == "__main__":
    inspect_dataset()