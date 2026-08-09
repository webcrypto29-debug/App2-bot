# 1. Base image (Python Version)
FROM python:3.10-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy all project files
COPY . .

# 5. Command to run the bot
CMD ["python", "app2.py"]
