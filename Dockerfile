FROM python:3.8

ARG REQUIREMENTS_TXT

COPY . /app
COPY ${REQUIREMENTS_TXT} /app/requirements.txt
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "-u", "app.py"]
