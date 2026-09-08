FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose ports
EXPOSE 5000 5001 5002

# Run all services
CMD sh -c "python src/dashboard/app.py & python src/platform_gateway.py & python src/admin/app.py & wait"
