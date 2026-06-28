# Use a lightweight official Python runtime as a base image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy requirements file first to utilize Docker layer cache
COPY requirements.txt .

# Install necessary libraries and dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Run the streamlit application when the container starts
CMD ["streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
