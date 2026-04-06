FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
# Force Streamlit to 8080 and bind to 0.0.0.0
CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8080", "--server.address=0.0.0.0"]
