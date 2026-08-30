from .razorpay_client import client


class RazorpayService:

    def get_payments(self, count=10):
        return client.payment.all({
            "count": count
        })

    def execute_recovery(self, payment, action):
        """
        Execute a recovery action for an approved payment.

        For the RecoverX prototype, the recovery action is modeled
        as a successful retry in Razorpay Test Mode.
        """
        if payment.status != "failed":
            return {
                "status": "failed",
                "message": "Recovery can only be executed for failed payments.",
                "recovered_amount": 0.0
            }


        if action not in {"delayed_retry", "immediate_retry"}:
            return {
                "status": "failed",
                "message": "Unsupported recovery action.",
                "recovered_amount": 0.0
            }

        return {
            "status": "success",
            "message": f"{action} executed successfully.",
            "recovered_amount": payment.amount
        }


razorpay_service = RazorpayService()