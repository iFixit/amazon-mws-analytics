FROM python:3.8-alpine AS base
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM base AS lint
RUN pip install --no-cache-dir pylint
COPY *.py ./
WORKDIR /
CMD ["pylint", "app"]

FROM base AS prod
COPY *.py ./
WORKDIR /
CMD ["python", "-m", "app"]
