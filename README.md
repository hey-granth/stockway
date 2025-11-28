# GEMINI Backend

## Project Overview

GEMINI is a robust, modular monolithic backend built with Django and Django REST Framework (DRF). It serves as the core infrastructure for a rural supply and delivery platform, connecting Shopkeepers, Warehouses, and Riders. The system handles order management, inventory tracking, geospatial delivery assignments, and automated payouts.

## Core Features

*   **Shopkeepers**: Browse inventory, place orders from nearby warehouses, and track deliveries.
*   **Warehouses**: Manage inventory, accept/reject orders, and oversee rider assignments.
*   **Riders**: Receive delivery assignments based on location, update status, and track earnings.
*   **Orders**: Full lifecycle management from creation to delivery with status tracking.
*   **Payments**: Automated payout calculations based on delivery distance and successful completion.
*   **Notifications**: Real-time system-wide notifications for all user roles.
*   **Analytics**: Comprehensive dashboards for system, warehouse, and rider performance metrics.

## Tech Stack

*   **Language**: Python 3.13+
*   **Framework**: Django 5.2, Django REST Framework 3.16
*   **Database**: PostgreSQL (with PostGIS support) / Supabase
*   **Caching & Queues**: Redis, Celery
*   **Authentication**: OTP-based (Supabase Auth / Custom)
*   **Geospatial**: `djangorestframework-gis`
*   **Testing**: Pytest

## Architecture Summary

The project follows a modular monolithic architecture. Each domain (orders, inventory, users) is encapsulated in its own Django app but shares a unified database and event bus.

*   **Synchronous API**: Handles immediate user requests (CRUD, reads).
*   **Async Pipeline**: Celery workers handle background tasks like analytics computation, notifications, and payout processing.

## API Documentation

Full API documentation is available on our static documentation site:

[**View API Documentation**](docs_site/index.html)

*(Note: If viewing locally, open `docs_site/index.html` in your browser)*

## Local Setup

### Prerequisites

*   Python 3.13+
*   PostgreSQL
*   Redis

### Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd backend
    ```

2.  **Create and activate a virtual environment**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Environment Variables**
    Create a `.env` file in the project root by copying the example:
    ```bash
    cp .env.example .env
    ```
    Update the `.env` file with your local database credentials and Supabase keys.

5.  **Database Setup**
    ```bash
    python manage.py migrate
    ```

6.  **Create Superuser**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Run the Development Server**
    ```bash
    python manage.py runserver
    ```

### Running Celery (Optional for Async Tasks)

Ensure Redis is running, then start the Celery worker:
```bash
celery -A backend worker -l info
```

## Running Tests

The project uses `pytest` for testing.

```bash
pytest --keepdb
```

## Deployment

The application is Docker-ready and can be deployed to platforms like Render, Railway, or AWS.

1.  **Build Docker Image**
    ```bash
    docker build -t gemini-backend .
    ```

2.  **Run Container**
    ```bash
    docker run -p 8000:8000 --env-file .env gemini-backend
    ```

## Folder Structure

```
.
├── accounts/         # User authentication and profiles
├── analytics/        # System and performance analytics
├── backend/          # Project settings and configuration
├── configs/          # Environment and app configurations
├── core/             # Shared utilities and base classes
├── delivery/         # Delivery tracking logic
├── docs_site/        # Static API documentation site
├── inventory/        # Warehouse inventory management
├── notifications/    # User notification system
├── orders/           # Order processing and lifecycle
├── payments/         # Payouts and financial records
├── riders/           # Rider management and location
├── shopkeepers/      # Shopkeeper specific views
├── warehouses/       # Warehouse administration
├── manage.py         # Django management script
├── requirements.txt  # Python dependencies
└── API_DOCUMENTATION.md # Markdown API reference
```

## License

MIT License
