import random
from datetime import datetime, timedelta

from .database import SessionLocal
from .models import Customer, Payment


FAILURE_REASONS = [
    "insufficient_funds",
    "temporary_failure",
    "authentication_failed",
    "card_expired",
    "network_error",
]

FIRST_NAMES = [
    "Aarav", "Vivaan", "Aditya", "Arjun", "Rahul",
    "Rohan", "Karan", "Neha", "Ananya", "Priya",
    "Ishita", "Sneha", "Aditi", "Kavya", "Riya",
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Mehta", "Kumar",
    "Verma", "Gupta", "Iyer", "Shah", "Nair",
]


def generate_dataset():
    db = SessionLocal()

    try:
        # Avoid duplicating the dataset if the script is run again.
        if db.query(Customer).filter(
            Customer.email == "dataset-marker@recoverx.local"
        ).first():
            print("Synthetic dataset already exists. Skipping generation.")
            return

        customers = []

        # Create 100 customers.
        for _ in range(100):
            name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            email = (
                name.lower().replace(" ", ".")
                + f"{random.randint(100, 999)}@example.com"
            )

            successful = random.randint(2, 15)
            failed = random.randint(0, 4)

            total_paid = successful * random.randint(999, 4999)

            reliability = successful / (successful + failed)

            customer = Customer(
                name=name,
                email=email,
                successful_payments=successful,
                failed_payments=failed,
                lifetime_value=float(total_paid),
                payment_reliability=round(reliability, 2),
            )

            db.add(customer)
            customers.append(customer)

        marker = Customer(
            name="RecoverX Dataset Marker",
            email="dataset-marker@recoverx.local",
            successful_payments=0,
            failed_payments=0,
            lifetime_value=0.0,
            payment_reliability=0.0,
        )

        db.add(marker)

        db.commit()

        for customer in customers:
            db.refresh(customer)

        # Create 600 payments.
        for _ in range(600):
            customer = random.choice(customers)

            amount = random.choice([
                499,
                999,
                1499,
                2499,
                3499,
                4999,
                7999,
                9999,
            ])

            # Roughly 65% successful, 35% failed.
            if random.random() < 0.65:
                status = "success"
                failure_reason = None
            else:
                status = "failed"
                failure_reason = random.choice(FAILURE_REASONS)

            attempt_count = (
                random.randint(0, 1)
                if status == "success"
                else random.randint(1, 3)
            )

            timestamp = (
                datetime.now() - timedelta(
                    days=random.randint(0, 90),
                    hours=random.randint(0, 23),
                )
            ).isoformat()

            payment = Payment(
                customer_id=customer.id,
                amount=float(amount),
                status=status,
                failure_reason=failure_reason,
                attempt_count=attempt_count,
                timestamp=timestamp,
                razorpay_payment_id=None,
            )

            db.add(payment)

        db.commit()

        print("Synthetic dataset created successfully.")
        print(f"Customers: {db.query(Customer).count()}")
        print(f"Payments: {db.query(Payment).count()}")

    finally:
        db.close()


if __name__ == "__main__":
    generate_dataset()