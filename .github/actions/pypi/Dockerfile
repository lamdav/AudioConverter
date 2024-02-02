FROM python:3.12-alpine

RUN apk add --no-cache \
  bash \
  git \
  gcc \
  libffi-dev \
  linux-headers \
  musl-dev \
  openssl-dev

RUN pip install --upgrade pip
RUN pip install --upgrade pipx
RUN pipx install poetry

RUN python --version
RUN pip --version
RUN pipx --version
RUN poetry --version

COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
