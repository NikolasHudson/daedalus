# Daedalus

A legal tech platform built with Django and AWS.

## Development Setup

### Local Setup

1. Clone the repository
2. Create virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Copy .env.example to .env and configure variables:
   ```
   cp .env.example .env
   ```
5. Run migrations:
   ```
   cd daedlaus
   python manage.py migrate
   ```
6. Start the development server:
   ```
   python manage.py runserver
   ```

### Docker Setup

1. Clone the repository
2. Create .env file:
   ```
   cp .env.example .env
   ```
3. Build and start containers:
   ```
   docker compose up --build
   ```
4. Access the application at http://localhost:8000

## Technologies Used

- Django 4.2.10
- PostgreSQL
- Django REST Framework
- Django Templates with HTMX
- Tailwind CSS with DaisyUI
- AWS Bedrock for AI capabilities