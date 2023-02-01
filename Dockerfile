FROM ubuntu:22.04

ENV LANG=en_US.UTF-8

RUN apt-get update \
  && DEBIAN_FRONTEND=noninteractive \
    apt-get install -y --no-install-recommends \
      python3-pip libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0 \
      python3.10-venv \
      shared-mime-info \
      fonts-font-awesome \
      fonts-freefont-otf \
      uwsgi \
      uwsgi-plugin-python3 \
      dumb-init \
      curl \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

EXPOSE 5001

WORKDIR /opt/weasyprint

RUN python3 -m venv /opt/weasyprint && \
  . ./bin/activate && \
  pip3 install --upgrade pip && \
  pip3 install wheel && \
  pip3 install WeasyPrint gunicorn flask

COPY *.py ./

ENTRYPOINT ["dumb-init", "--"]
CMD ["/bin/bash", "-c", ". ./bin/activate && gunicorn --bind 0.0.0.0:5001 --timeout 90 --graceful-timeout 60 app:app"]

