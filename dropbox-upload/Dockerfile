ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache python3 python3-dev
RUN pip3 install \
      arrow \
      dropbox \
      requests \
      retrace;

COPY upload.py /

CMD python3 /upload.py
