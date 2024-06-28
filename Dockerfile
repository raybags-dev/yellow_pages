# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Setting working directory inside the container
WORKDIR /app

# Copying all files from current directory to /app in the container
COPY . /app

# Installing Python dependencies from requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright and its dependencies
RUN pip install playwright
RUN playwright install

# Expose port 5000
EXPOSE 5000

# Set environment variable (optional)
ENV NAME yellow-pages-profiler

CMD ["python", "main.py"]
