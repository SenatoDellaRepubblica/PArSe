FROM python:3.9-slim-buster
MAINTAINER Roberto Battistoni <roberto.battistoni@senato.it>
RUN apt-get update && apt-get upgrade -y && apt-get install -y python3-dev build-essential

WORKDIR /usr/src/app
RUN mkdir ./log
RUN touch ./log.txt

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . ./
CMD [ "python", "parse_web.py"]