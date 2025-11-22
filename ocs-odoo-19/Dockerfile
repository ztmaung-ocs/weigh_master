FROM odoo:19.0

USER root
RUN apt-get update && apt-get install -y nano htop && \
    pip3 install --break-system-packages paho-mqtt
USER odoo