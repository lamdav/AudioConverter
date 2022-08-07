FROM python:3.9-alpine

RUN apk add --no-cache \
  bash \
  git \
  gcc \
  libffi-dev \
  linux-headers \
  musl-dev

RUN pip install --upgrade pip
RUN pip install --upgrade black==22.6.0

RUN python --version
RUN pip --version

COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
