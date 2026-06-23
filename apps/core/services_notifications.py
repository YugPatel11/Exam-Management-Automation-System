"""
Notification Service.
Handles sending emails/SMS and logging them.
"""
from django.core.mail import send_mail
from django.conf import settings
from apps.core.models_audit import NotificationLog


class NotificationService:
    @staticmethod
    def send_email(user, subject, message):
        """
        Sends an email and logs it.
        """
        log = NotificationLog.objects.create(
            user=user,
            notification_type='email',
            subject=subject,
            message=message,
            status='pending'
        )
        
        try:
            # In a real app, this would use a background task like Celery
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            log.status = 'sent'
        except Exception as e:
            log.status = 'failed'
            log.error_message = str(e)
            
        log.save()
        return log.status == 'sent'

    @staticmethod
    def send_sms(user, message):
        """
        Sends an SMS and logs it. (Mock implementation)
        """
        # SMS integration would go here (e.g., Twilio, AWS SNS)
        log = NotificationLog.objects.create(
            user=user,
            notification_type='sms',
            subject="SMS Notification",
            message=message,
            status='sent' # Mock success
        )
        return True
