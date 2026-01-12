FROM python:3.11-slim

WORKDIR /app

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Expose port (Koyeb usually defaults to 8000)
EXPOSE 8000

# Run Streamlit on port 8000
CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8000", "--server.address=0.0.0.0"]
