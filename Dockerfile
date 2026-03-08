FROM python:3.14-slim-trixie

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY radio_web.py .
COPY lang.py .
COPY style.css .
COPY audio_handler.js .
COPY .streamlit/ ./.streamlit/


EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "/app/radio_web.py"]
