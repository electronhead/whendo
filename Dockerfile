# https://hub.docker.com/_/python

FROM python:3.9.0

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app
COPY ./mothership ./mothership

CMD [ "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" ]