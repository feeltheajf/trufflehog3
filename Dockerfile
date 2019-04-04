FROM python:3-alpine
RUN apk add --no-cache git && pip install trufflehog3
RUN adduser -S truffleHog
USER truffleHog
WORKDIR /proj
ENTRYPOINT [ "trufflehog" ]
CMD [ "-h" ]
