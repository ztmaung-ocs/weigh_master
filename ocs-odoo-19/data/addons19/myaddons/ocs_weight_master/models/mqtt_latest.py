from odoo import models, fields, api

class MqttLatest(models.Model):
    _name = "weight.latest"
    _description = "Latest Weight Data (Temporary)"
    _rec_name = "weight"
    _table = "weight_latest"

    weight = fields.Float(string="Latest MQTT Weight", digits=(16, 3), readonly=True)
    timestamp = fields.Datetime(string="Timestamp", readonly=True)
    raw_data = fields.Text(string="Raw Data", readonly=True)
    input_weight = fields.Float(string="Weight", digits=(16, 3), help="Enter weight or click Fetch Data to get latest MQTT weight")

    @api.model
    def get_latest(self):
        """Get or create the singleton record"""
        record = self.search([], limit=1)
        if not record:
            record = self.create({
                'weight': 0.0,
                'timestamp': fields.Datetime.now(),
                'raw_data': '',
            })
        return record

    @api.model
    def update_latest(self, weight, raw_data=None):
        """Update the latest MQTT data"""
        record = self.get_latest()
        record.write({
            'weight': weight,
            'timestamp': fields.Datetime.now(),
            'raw_data': raw_data or '',
        })
        return record

    def action_fetch_data(self):
        """Fetch latest MQTT weight data into the input field"""
        self.ensure_one()
        # Get the latest MQTT data (singleton record)
        latest_record = self.get_latest()
        
        # Invalidate cache to get fresh data from database
        latest_record.invalidate_recordset(['weight', 'timestamp'])
        
        # Read fresh data directly from database using SQL to bypass cache
        self.env.cr.execute("""
            SELECT weight, timestamp 
            FROM weight_latest 
            WHERE id = %s
        """, (latest_record.id,))
        result = self.env.cr.fetchone()
        
        if result:
            fresh_weight, fresh_timestamp = result
            
            # Update all fields including readonly ones using sudo
            self.sudo().write({
                'input_weight': fresh_weight,
                'weight': fresh_weight,
                'timestamp': fresh_timestamp,
            })
            
            message = f'Weight {fresh_weight} fetched from MQTT'
        else:
            message = 'No MQTT data found'
        
        # Return action to reload the form with updated data
        # This will refresh the form and show the updated values
        return {
            'type': 'ir.actions.act_window',
            'name': 'Entrance Form',
            'res_model': 'weight.latest',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('ocs_weight_master.view_mqtt_latest_form').id,
            'target': 'current',
        }

    def action_refresh_data(self):
        """Refresh the form with latest MQTT data - only updates weight and timestamp"""
        self.ensure_one()
        # Store old values
        old_weight = self.weight
        old_timestamp = self.timestamp
        
        # Invalidate cache and read fresh data
        self.invalidate_recordset(['weight', 'timestamp'])
        
        # Read fresh data from database by browsing the record again
        fresh_record = self.browse(self.id)
        
        # Update the record with fresh data
        if fresh_record.weight != old_weight or fresh_record.timestamp != old_timestamp:
            self.write({
                'weight': fresh_record.weight,
                'timestamp': fresh_record.timestamp,
            })
            message = f'Weight updated to {fresh_record.weight}'
        else:
            message = f'Weight is already up to date: {fresh_record.weight}'
        
        # Return notification without reloading the form
        # The form will automatically update because we wrote to the record
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Refreshed',
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_save_to_record(self):
        """Save the input weight data to weight.record"""
        self.ensure_one()
        # Use input_weight if available, otherwise use weight
        weight_to_save = self.input_weight if self.input_weight else self.weight
        
        if not weight_to_save or weight_to_save == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Warning',
                    'message': 'No weight data to save.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        weight_record = self.env['weight.record'].create({
            'weight': weight_to_save,
            'source': 'mqtt',
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Saved',
                'message': f'Weight {weight_to_save} saved successfully.',
                'type': 'success',
                'sticky': False,
            }
        }

