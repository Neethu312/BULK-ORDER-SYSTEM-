# Asynchronous Bulk Order Processing API

This is a Django REST Framework project that provides an API for managing users, customers, and orders. Its main feature is an endpoint for asynchronously processing bulk order uploads from either a **JSON body** or a **CSV file** using Celery and Redis.

## Core Features
- User and Customer Management
- Token-based Authentication (`rest_framework.authtoken`)
- Asynchronous Task Processing with Celery
- Dual-format Bulk Upload Endpoint (`/api/orders/bulk-upload/`)
- Task Status Tracking API

## Project Setup

1.  **Clone the repository:**
    `git clone <your-github-repo-url>`

2.  **Set up the environment:**
    `python3 -m venv venv`
    `source venv/bin/activate`

3.  **Install dependencies:**
    `pip install -r requirements.txt`

4.  **Run migrations:**
    `python manage.py migrate`

5.  **Start the services (each in a separate terminal):**
    *   Django Server: `python manage.py runserver`
    *   Celery Worker: `celery -A bulkorder worker -l info`
    *   Redis Server: `redis-server` (if not already running)

## API Usage

*   **Login**: `POST /api/login/`
*   **Bulk Upload**: `POST /api/orders/bulk-upload/` (Accepts JSON or a CSV file)
*   **Task Status**: `GET /api/tasks/<task_id>/`
```
