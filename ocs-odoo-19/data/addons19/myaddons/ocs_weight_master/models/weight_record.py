from odoo import models, fields, api
from .mqtt_service import MqttWeightService

class WeightRecord(models.Model):
    _name = "weight.record"
    _description = "Incoming Weight from MQTT"
    _order = "create_date desc, id desc"

    weight = fields.Float(required=True, digits=(16, 3))
    source = fields.Selection([
        ('mqtt', 'MQTT'),
        ('manual', 'Manual')
    ], string="Source", default='mqtt', required=True)
    create_date = fields.Datetime(readonly=True)

    @api.model
    def get_latest_mqtt_record(self):
        """Returns the latest MQTT weight record"""
        return self.search([('source', '=', 'mqtt')], limit=1, order='create_date desc, id desc')

    def action_open_mqtt_form(self):
        """Action to open the latest MQTT record in form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Entrance Form',
            'res_model': 'weight.record',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('ocs_weight_master.view_weight_record_mqtt_form').id,
            'target': 'current',
        }

    @api.model
    def action_open_latest_mqtt_form(self):
        """Action to open the latest MQTT record in form view"""
        latest = self.get_latest_mqtt_record()
        if latest:
            return latest.action_open_mqtt_form()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Entrance Form',
            'res_model': 'weight.record',
            'view_mode': 'form',
            'view_id': self.env.ref('ocs_weight_master.view_weight_record_mqtt_form').id,
            'target': 'current',
        }

    @api.model
    def _register_hook(self):
        res = super()._register_hook()
        MqttWeightService.start(self.env)
        return res
