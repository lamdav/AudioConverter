FROM python:3.7-alpine

RUN apk add --no-cache \
  bash \
  git \
  gcc \
  libffi-dev \
  linux-headers \
  musl-dev \
  openssl-dev

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools wheel twine

RUN python --version
RUN pip --version
RUN twine --version

COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
