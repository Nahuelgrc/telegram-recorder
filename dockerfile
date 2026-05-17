FROM python:3.10-slim
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
RUN pip install flask requests
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]