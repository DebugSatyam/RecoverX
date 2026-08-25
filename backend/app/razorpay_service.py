from .razorpay_client import client


class RazorpayService:

    def get_payments(self, count=10):
        return client.payment.all({
            "count": count
        })


razorpay_service = RazorpayService()