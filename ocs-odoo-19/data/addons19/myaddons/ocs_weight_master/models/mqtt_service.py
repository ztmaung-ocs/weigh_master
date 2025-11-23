import json
import logging
import os
import threading
import time
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

# Defaults; can be overridden with environment variables, system parameters, or defaults
DEFAULT_BROKER = "192.168.101.85"
DEFAULT_PORT = 1883
DEFAULT_TOPIC = "weight/master"
DEFAULT_KEEPALIVE = 60
DEFAULT_USERNAME = None
DEFAULT_PASSWORD = None


class MqttWeightService:
    """Singleton MQTT listener running in a background daemon thread.

    Reads JSON payloads like:
      {"weight":84,"raw":"000000","hex":"...","timestamp":1763808861091}
    and stores them in weight.record.
    """

    _thread = None
    _stop_flag = False
    _client = None

    @classmethod
    def _get_params(cls, env):
        """Get MQTT parameters from environment variables, system parameters, or defaults.
        Priority: Environment variables > System parameters > Defaults
        """
        ICP = env["ir.config_parameter"].sudo()
        
        # Check environment variables first (from docker-compose)
        broker = os.getenv("MQTT_BROKER") or ICP.get_param("ocs_weight_master.mqtt_broker", DEFAULT_BROKER)
        port_str = os.getenv("MQTT_PORT") or ICP.get_param("ocs_weight_master.mqtt_port", str(DEFAULT_PORT))
        topic = os.getenv("MQTT_TOPIC") or ICP.get_param("ocs_weight_master.mqtt_topic", DEFAULT_TOPIC)
        keepalive_str = os.getenv("MQTT_KEEPALIVE") or ICP.get_param("ocs_weight_master.mqtt_keepalive", str(DEFAULT_KEEPALIVE))
        username = os.getenv("MQTT_USERNAME") or ICP.get_param("ocs_weight_master.mqtt_username", DEFAULT_USERNAME)
        password = os.getenv("MQTT_PASSWORD") or ICP.get_param("ocs_weight_master.mqtt_password", DEFAULT_PASSWORD)
        
        try:
            port = int(port_str)
        except (ValueError, TypeError):
            port = DEFAULT_PORT
            
        try:
            keepalive = int(keepalive_str)
        except (ValueError, TypeError):
            keepalive = DEFAULT_KEEPALIVE
        
        auth_info = f"with user '{username}'" if username else "without authentication"
        _logger.info("MQTT Configuration - Broker: %s, Port: %s, Topic: %s, %s (from %s)", 
                    broker, port, topic, auth_info,
                    "environment" if os.getenv("MQTT_BROKER") else "config_parameter")
        
        return broker, port, topic, keepalive, username, password

    @classmethod
    def start(cls, env):
        if cls._thread and cls._thread.is_alive():
            _logger.info("MQTT listener already running.")
            return

        broker, port, topic, keepalive, username, password = cls._get_params(env)
        cls._stop_flag = False

        def _run():
            _logger.info("Starting OCS Weight Master MQTT listener: %s:%s topic=%s", broker, port, topic)

            client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            cls._client = client

            # Set username and password if provided
            if username:
                client.username_pw_set(username, password)

            def on_connect(client, userdata, flags, reason_code, properties=None):
                if reason_code == 0:
                    _logger.info("MQTT connected.")
                    client.subscribe(topic, qos=0)
                else:
                    _logger.error("MQTT connect failed: %s", reason_code)

            def on_message(client, userdata, msg):
                try:
                    payload = msg.payload.decode("utf-8", errors="replace")
                    data = json.loads(payload)

                    weight = float(data.get("weight", 0))
                    
                    registry = env.registry
                    with registry.cursor() as cr:
                        thread_env = api.Environment(cr, SUPERUSER_ID, {})
                        # Update latest MQTT data instead of creating records
                        thread_env["weight.latest"].update_latest(weight, payload)
                        cr.commit()

                    _logger.info("Updated latest weight %.3f from MQTT.", weight)

                except Exception:
                    _logger.exception("Failed to process MQTT message: %r", msg.payload)

            client.on_connect = on_connect
            client.on_message = on_message

            while not cls._stop_flag:
                try:
                    client.connect(broker, port, keepalive=keepalive)
                    client.loop_forever(retry_first_connection=True)
                except Exception as e:
                    _logger.warning("MQTT error: %s. Reconnecting in 5 seconds...", e)
                    time.sleep(5)

        cls._thread = threading.Thread(target=_run, daemon=True, name="OCS-Weight-Master-MQTT")
        cls._thread.start()

    @classmethod
    def stop(cls):
        cls._stop_flag = True
        try:
            if cls._client:
                cls._client.disconnect()
        except Exception:
            pass
