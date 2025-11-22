OCS Weight Master (Odoo 19)
=============================

This module subscribes to an MQTT topic and stores incoming weight messages.

Default settings:
- Broker: 192.168.101.85
- Port: 1883
- Topic: weight/master

Payload format:
    {"weight":84,"raw":"000000","hex":"022b...","timestamp":1763808861091}

System parameters you can set in Odoo:
- ocs_weight_master.mqtt_broker
- ocs_weight_master.mqtt_port
- ocs_weight_master.mqtt_topic
- ocs_weight_master.mqtt_keepalive
