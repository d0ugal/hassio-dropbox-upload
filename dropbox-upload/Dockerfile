ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

RUN apk add --no-cache python3 python3-dev
RUN pip3 install dropbox retrace

COPY upload.py /

CMD echo 'nameserver 1.1.1.1' > /etc/resolv.conf && python3 /upload.py
