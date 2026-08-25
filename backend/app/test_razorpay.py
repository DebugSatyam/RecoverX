from .razorpay_service import razorpay_service


def test_connection():
    try:
        response = razorpay_service.get_payments(count=1)

        print("Razorpay service connection successful.")
        print(f"Response received: {response}")

    except Exception as error:
        print("Razorpay service connection failed.")
        print(f"Error: {error}")


if __name__ == "__main__":
    test_connection()