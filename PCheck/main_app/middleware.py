from django.utils import timezone

from . import models


class BookingCleanupMiddleware:
    """
    On each request, free PCs with bookings whose end_time has passed and
    that have not been marked as expired yet. Mirrors clearup_pcs view logic.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            now = timezone.now()
            expired_bookings = models.Booking.objects.filter(end_time__lt=now, expiry__isnull=True)
            for booking in expired_bookings.select_related('pc'):
                pc = booking.pc
                if pc and pc.booking_status != 'available':
                    pc.booking_status = 'available'
                    pc.save(update_fields=["booking_status"])
                booking.expiry = booking.end_time
                booking.save(update_fields=["expiry"])
        except Exception:
            # Silently ignore cleanup errors to not impact user requests
            pass

        response = self.get_response(request)
        return response




