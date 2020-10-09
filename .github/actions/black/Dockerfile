FROM python:3.8-alpine

RUN apk add --no-cache \
  bash \
  git \
  gcc \
  libffi-dev \
  linux-headers \
  musl-dev

RUN pip install --upgrade pip
RUN pip install --upgrade black==20.8b1

RUN python --version
RUN pip --version

COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
