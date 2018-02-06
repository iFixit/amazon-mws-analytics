FROM alpine:latest

RUN apk update && apk add python3 && mkdir -p /opt/amazon-mws-analytics
COPY . /opt/amazon-mws-analytics

WORKDIR /opt
RUN cd /opt/amazon-mws-analytics && pip3 install -r requirements.txt

ENTRYPOINT python3 -m amazon-mws-analytics
