import time
import logging

logger = logging.getLogger(__name__)


def send_due_reminder(task_title):
    """
    Background job that simulates sending a notification.
    Waits 5 seconds then logs a reminder message.
    """
    time.sleep(5)
    reminder_message = f"Reminder: Task '{task_title}' is due soon!"
    logger.info(reminder_message)
    print(reminder_message)
