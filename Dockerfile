FROM python:3.8-alpine AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS dev
# Alas, black depends on regex, which doesn't have an Alpine wheel, which means
# we need to compile it, which means we need a build environment.
RUN apk add --no-cache --virtual .black-build-deps gcc musl-dev \
   && pip install --prefer-binary --no-cache-dir pylint black isort \
   && apk del --no-cache .black-build-deps
WORKDIR /

FROM base AS prod
COPY *.py ./
WORKDIR /
CMD ["python", "-m", "app"]
