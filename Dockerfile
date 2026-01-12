FROM python:3.11-slim

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose port (GCP defaults to 8080)
EXPOSE 8080

# Run Streamlit on port 8080
CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8080", "--server.address=0.0.0.0"]
