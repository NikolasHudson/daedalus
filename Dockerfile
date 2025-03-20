# Stage 1: Base build stage
FROM python:3.11-slim AS builder

# Install Node.js and npm for Tailwind CSS
RUN apt-get update && apt-get install -y nodejs npm && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create the app directory
RUN mkdir /app

# Set the working directory
WORKDIR /app

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

# Upgrade pip and install dependencies
RUN pip install --upgrade pip 

# Copy the requirements file first (better caching)
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Production stage
FROM python:3.11-slim

# Install Node.js and npm for Tailwind CSS
RUN apt-get update && apt-get install -y nodejs npm && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN useradd -m -r appuser && \
   mkdir /app && \
   chown -R appuser /app

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Set the working directory
WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Set environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1 

# Create Tailwind theme app if it doesn't exist
RUN cd daedlaus && python manage.py tailwind install --no-input

# Build Tailwind CSS
RUN cd daedlaus && python manage.py tailwind build --no-input

# Collect static files
RUN cd daedlaus && python manage.py collectstatic --noinput

# Prepare migrations
RUN cd daedlaus && python manage.py makemigrations

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000 

# Start the application using Gunicorn
CMD ["sh", "-c", "cd daedlaus && python manage.py migrate && gunicorn --bind 0.0.0.0:8000 --workers 3 daedlaus.wsgi:application"]