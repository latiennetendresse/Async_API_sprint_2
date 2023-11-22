FROM python:3.10

WORKDIR /opt/tests

RUN groupadd -r web && useradd -d /opt/tests -r -g web web \
    && chown web:web -R /opt/tests

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt requirements.txt

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

USER web

ENTRYPOINT ["pytest", "src"]
