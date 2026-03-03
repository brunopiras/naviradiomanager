FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir streamlit requests


COPY radio_web.py .
COPY lang.py .

EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "radio_web.py", "--server.port=8501", "--server.address=0.0.0.0", "--client.toolbarMode=hidden"]