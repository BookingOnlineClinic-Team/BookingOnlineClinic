from celery import shared_task

from bookingonline.models import dao
import utils


@shared_task
def check_pending_refunds():
    payments = dao.get_pending_refund_payments()
    for payment in payments:
        utils.check_and_confirm_payout(payment)
    return f"Checked {len(payments)} pending refund payments"
