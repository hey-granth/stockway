#!/bin/bash

# Notification System Management Script
# Quick commands for managing the notification pipeline

set -e

PROJECT_DIR="/home/granth/PycharmProjects/backend"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
VENV_CELERY="$PROJECT_DIR/.venv/bin/celery"

cd "$PROJECT_DIR"

case "$1" in
    setup)
        echo "Setting up notification system..."
        echo "1. Installing dependencies..."
        .venv/bin/pip install celery kombu

        echo "2. Running migrations..."
        $VENV_PYTHON manage.py makemigrations notifications
        $VENV_PYTHON manage.py migrate

        echo "✓ Setup complete!"
        echo ""
        echo "Next steps:"
        echo "1. Start RabbitMQ: sudo systemctl start rabbitmq-server"
        echo "2. Start Redis: sudo systemctl start redis-server"
        echo "3. Start worker: ./notifications/manage_notifications.sh worker"
        ;;

    worker)
        echo "Starting Celery worker..."
        $VENV_CELERY -A backend worker -l info -Q notifications
        ;;

    beat)
        echo "Starting Celery beat (periodic tasks)..."
        $VENV_CELERY -A backend beat -l info
        ;;

    flower)
        echo "Starting Flower monitoring..."
        if ! command -v $VENV_DIR/bin/flower &> /dev/null; then
            echo "Installing Flower..."
            .venv/bin/pip install flower
        fi
        $VENV_CELERY -A backend flower
        ;;

    test)
        echo "Running notification tests..."
        $VENV_PYTHON manage.py test notifications
        ;;

    migrate)
        echo "Running migrations..."
        $VENV_PYTHON manage.py makemigrations notifications
        $VENV_PYTHON manage.py migrate
        ;;

    shell-test)
        echo "Testing notification in Django shell..."
        $VENV_PYTHON manage.py shell <<EOF
from notifications.tasks import send_notification_task
from accounts.models import User

user = User.objects.first()
if user:
    result = send_notification_task.delay(
        user.id,
        "Test Notification",
        "This is a test message from the shell",
        "system"
    )
    print(f"Task ID: {result.id}")
    print("Check Celery worker logs for task execution")
else:
    print("No users found. Create a user first.")
EOF
        ;;

    status)
        echo "Checking service status..."
        echo ""
        echo "=== RabbitMQ ==="
        if systemctl is-active --quiet rabbitmq-server; then
            echo "✓ Running"
        else
            echo "✗ Not running"
        fi

        echo ""
        echo "=== Redis ==="
        if systemctl is-active --quiet redis-server; then
            echo "✓ Running"
        else
            echo "✗ Not running"
        fi

        echo ""
        echo "=== Database ==="
        if $VENV_PYTHON -c "from django.db import connection; connection.ensure_connection()" 2>/dev/null; then
            echo "✓ Connected"
        else
            echo "✗ Not connected"
        fi
        ;;

    stats)
        echo "Notification statistics..."
        $VENV_PYTHON manage.py shell <<EOF
from notifications.models import Notification
from django.db.models import Count

total = Notification.objects.count()
unread = Notification.objects.filter(is_read=False).count()
by_type = Notification.objects.values('type').annotate(count=Count('id'))

print(f"\nTotal notifications: {total}")
print(f"Unread notifications: {unread}")
print(f"Read notifications: {total - unread}")
print("\nBy type:")
for item in by_type:
    print(f"  {item['type']}: {item['count']}")
EOF
        ;;

    cleanup)
        echo "Running notification cleanup..."
        $VENV_PYTHON manage.py shell <<EOF
from notifications.tasks import cleanup_old_notifications_task
result = cleanup_old_notifications_task()
print(f"Cleaned up {result['deleted_count']} notifications")
EOF
        ;;

    *)
        echo "Notification System Management"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  setup        - Initial setup (install deps, run migrations)"
        echo "  worker       - Start Celery worker"
        echo "  beat         - Start Celery beat (periodic tasks)"
        echo "  flower       - Start Flower monitoring UI"
        echo "  test         - Run notification tests"
        echo "  migrate      - Run database migrations"
        echo "  shell-test   - Test notification in Django shell"
        echo "  status       - Check service status"
        echo "  stats        - Show notification statistics"
        echo "  cleanup      - Run manual cleanup of old notifications"
        echo ""
        echo "Examples:"
        echo "  $0 setup     # Initial setup"
        echo "  $0 worker    # Start worker in foreground"
        echo "  $0 stats     # Show statistics"
        exit 1
        ;;
esac

