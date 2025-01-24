FROM python:3.10-alpine

ENV WORK_DIR=workdir \
  HASSIO_DATA_PATH=/data

RUN mkdir -p ${WORK_DIR}
WORKDIR /${WORK_DIR}
COPY requirements.txt .

# RUN apk add --no-cache git \
#     && git clone https://github.com/stephan-carstens/modbus-mqtt.git /tmp/modbus-mqtt \
#     && cp /tmp/modbus-mqtt/*.py . \
#     && rm -rf /tmp/modbus-mqtt \
#     && apk del git

# install python libraries
RUN pip3 install -r requirements.txt

# Copy code
COPY modbus_mqtt/ ./
COPY src/  ./
COPY run.sh  ./


# Run
RUN chmod a+x run.sh
CMD [ "sh", "./run.sh" ]
