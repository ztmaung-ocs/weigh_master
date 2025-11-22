from . import models

def start_mqtt(env):
    """Odoo 19 post_init_hook gets env only."""
    from .models.mqtt_service import MqttWeightService
    MqttWeightService.start(env)
