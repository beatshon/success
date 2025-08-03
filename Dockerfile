FROM python:3.9-slim
WORKDIR /app
COPY requirements_aws.txt .
RUN pip install -r requirements_aws.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "simple_server:app"]
