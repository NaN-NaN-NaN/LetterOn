"""
LetterOn Server - Reminder Scheduler
Purpose: Background task to check and process reminders
Testing: Disabled in test environment
AWS Deployment: Use separate Lambda with EventBridge for production

This module provides:
- Background scheduler using APScheduler
- Checks reminders every minute
- Marks reminders as sent after processing

For production:
- Deploy reminder_worker Lambda function
- Create EventBridge rule: rate(1 minute)
- Lambda should call this check_and_process_reminders function
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.settings import settings
from app.services.dynamo import dynamodb_client
from app.utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def check_and_process_reminders():
    """
    Check for pending reminders and process them.

    This function:
    1. Queries DynamoDB for reminders that are due
    2. Processes each reminder (log for now, can add email/push notifications)
    3. Marks reminders as sent

    Note: For production, this should be a separate Lambda function
    that sends actual notifications via SNS, SES, or push notifications.
    """
    try:
        current_time = get_current_timestamp()
        logger.info(f"Checking for reminders at {current_time}")

        # Get all pending reminders
        pending_reminders = dynamodb_client.get_pending_reminders(current_time)

        if not pending_reminders:
            logger.debug("No pending reminders found")
            return

        logger.info(f"Found {len(pending_reminders)} pending reminders")

        # Process each reminder
        for reminder in pending_reminders:
            try:
                reminder_id = reminder["reminder_id"]
                user_id = reminder["user_id"]
                letter_id = reminder["letter_id"]
                message = reminder.get("message", "You have a reminder for a letter")

                # TODO: Send actual notification here
                # Examples:
                # - Send email via SES
                # - Send push notification via SNS
                # - Trigger webhook
                logger.info(
                    f"Processing reminder {reminder_id} for user {user_id}, letter {letter_id}: {message}"
                )

                # Mark reminder as sent
                dynamodb_client.update_reminder(
                    reminder_id=reminder_id,
                    updates={"sent": True, "sent_at": get_current_timestamp()}
                )

                logger.info(f"Reminder {reminder_id} marked as sent")

            except Exception as e:
                logger.error(f"Error processing reminder {reminder.get('reminder_id')}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Error checking reminders: {str(e)}", exc_info=True)


def start_reminder_scheduler():
    """
    Start the background reminder scheduler.

    Runs check_and_process_reminders every N seconds (configured in settings).
    """
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    scheduler = BackgroundScheduler()

    # Add job to check reminders
    scheduler.add_job(
        func=check_and_process_reminders,
        trigger=IntervalTrigger(seconds=settings.reminder_check_interval_seconds),
        id='reminder_checker',
        name='Check and process pending reminders',
        replace_existing=True
    )

    scheduler.start()
    logger.info(
        f"Reminder scheduler started (interval: {settings.reminder_check_interval_seconds}s)"
    )


def stop_reminder_scheduler():
    """Stop the background reminder scheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Reminder scheduler stopped")


# For AWS Lambda deployment (optional)
def lambda_handler(event, context):
    """
    Lambda handler for reminder worker.

    Deploy this as a separate Lambda function and trigger it with EventBridge.

    EventBridge Rule:
    - Schedule expression: rate(1 minute)
    - Target: This Lambda function

    IAM Permissions needed:
    - DynamoDB: Query, UpdateItem (on LetterOn-Reminders table)
    - CloudWatch Logs: CreateLogGroup, CreateLogStream, PutLogEvents
    - (Optional) SES/SNS: SendEmail, Publish for notifications
    """
    try:
        logger.info("Reminder worker Lambda invoked")
        check_and_process_reminders()

        return {
            "statusCode": 200,
            "body": "Reminders processed successfully"
        }

    except Exception as e:
        logger.error(f"Error in reminder worker Lambda: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": f"Error processing reminders: {str(e)}"
        }
