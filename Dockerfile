FROM python:3.6-slim

RUN apt-get update && apt-get install -y git

WORKDIR /trufflehog3
ADD . /trufflehog3
RUN pip install .

ENTRYPOINT [ "trufflehog3", "/source" ]
CMD [ "" ]
