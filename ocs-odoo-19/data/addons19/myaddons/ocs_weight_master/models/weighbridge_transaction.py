from odoo import models, fields, api
from datetime import datetime

class WeighbridgeTransaction(models.Model):
    _name = "weighbridge.transaction"
    _description = "Weighbridge Transaction"
    _order = "create_date desc, id desc"
    _rec_name = "voucher_no"

    voucher_no = fields.Char(string="Voucher No", required=True, readonly=True, copy=False, default='New')
    vehicle_no = fields.Char(string="Vehicle No", required=True)
    
    # Driver fields
    driver_name = fields.Char(string="Driver Name")
    driver_nrc = fields.Char(string="NRC")
    driver_phone = fields.Char(string="Phone Number")
    
    # Company/Customer
    company_name = fields.Char(string="Company Name")
    partner_id = fields.Many2one('res.partner', string="Customer", help="Select customer")
    
    # Responsible Employee
    responsible_id = fields.Many2one('hr.employee', string="Responsible", help="Select employee")
    
    deliver_to = fields.Text(string="Deliver To")
    
    type = fields.Selection([
        ('in', 'In'),
        ('out', 'Out'),
        ('in_out', 'In-Out'),
        ('visit', 'Visit')
    ], string="Type", required=True, default='in')
    
    product_ids = fields.Many2many('product.product', string="Products")
    
    remark1 = fields.Text(string="Remark 1")
    remark2 = fields.Text(string="Remark 2")
    
    entrance_weight = fields.Float(string="Entrance Weight", digits=(16, 3))
    exit_weight = fields.Float(string="Exit Weight", digits=(16, 3))
    net_weight = fields.Float(string="Net Weight", digits=(16, 3), compute="_compute_net_weight", store=True)
    
    entrance_date = fields.Datetime(string="Entrance Date")
    exit_date = fields.Datetime(string="Exit Date")
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('entrance', 'Entrance'),
        ('exit', 'Exit'),
        ('completed', 'Completed')
    ], string="State", default='draft', required=True)
    
    @api.depends('entrance_weight', 'exit_weight', 'type')
    def _compute_net_weight(self):
        for record in self:
            if record.type == 'in':
                record.net_weight = record.entrance_weight or 0.0
            elif record.type == 'out':
                record.net_weight = record.exit_weight or 0.0
            elif record.type == 'in_out':
                record.net_weight = (record.exit_weight or 0.0) - (record.entrance_weight or 0.0)
            else:
                record.net_weight = 0.0

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update company_name when partner is selected"""
        if self.partner_id:
            self.company_name = self.partner_id.name

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate voucher numbers"""
        for vals in vals_list:
            if vals.get('voucher_no', 'New') == 'New':
                # Generate voucher number: YYYYMMDDHHMMSS (datetime only)
                now = datetime.now()
                vals['voucher_no'] = now.strftime('%Y%m%d%H%M%S')
        return super(WeighbridgeTransaction, self).create(vals_list)

    def action_fetch_entrance_weight(self):
        """Fetch entrance weight from latest MQTT data"""
        self.ensure_one()
        latest_record = self.env['weight.latest'].get_latest()
        
        # Invalidate cache to get fresh data
        latest_record.invalidate_recordset(['weight', 'timestamp'])
        
        # Read fresh data from database
        self.env.cr.execute("""
            SELECT weight, timestamp 
            FROM weight_latest 
            WHERE id = %s
        """, (latest_record.id,))
        result = self.env.cr.fetchone()
        
        if result:
            fresh_weight, fresh_timestamp = result
            self.write({
                'entrance_weight': fresh_weight,
                'entrance_date': fresh_timestamp,
                'state': 'entrance',
            })
            message = f'Entrance weight {fresh_weight} fetched successfully'
        else:
            message = 'No weight data found'
        
        # Reload the form to show updated data
        return {
            'type': 'ir.actions.act_window',
            'name': 'Entrance Form',
            'res_model': 'weighbridge.transaction',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('ocs_weight_master.view_weighbridge_transaction_entrance_form').id,
            'target': 'current',
        }

    def action_fetch_exit_weight(self):
        """Fetch exit weight from latest MQTT data"""
        self.ensure_one()
        latest_record = self.env['weight.latest'].get_latest()
        
        # Invalidate cache to get fresh data
        latest_record.invalidate_recordset(['weight', 'timestamp'])
        
        # Read fresh data from database
        self.env.cr.execute("""
            SELECT weight, timestamp 
            FROM weight_latest 
            WHERE id = %s
        """, (latest_record.id,))
        result = self.env.cr.fetchone()
        
        if result:
            fresh_weight, fresh_timestamp = result
            self.write({
                'exit_weight': fresh_weight,
                'exit_date': fresh_timestamp,
                'state': 'exit' if self.state == 'entrance' else 'completed',
            })
            message = f'Exit weight {fresh_weight} fetched successfully'
        else:
            message = 'No weight data found'
        
        # Reload the form to show updated data
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exit Form',
            'res_model': 'weighbridge.transaction',
            'res_id': self.id,
            'view_mode': 'form',
            'view_id': self.env.ref('ocs_weight_master.view_weighbridge_transaction_exit_form').id,
            'target': 'current',
        }

    def action_print_entrance(self):
        """Open entrance form report in new window for POS printing"""
        self.ensure_one()
        report = self.env.ref('ocs_weight_master.action_report_weighbridge_transaction_entrance')
        url = f'/report/html/{report.report_name}/{self.id}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

    def action_print_all_data(self):
        """Open full transaction report in new window for POS printing"""
        self.ensure_one()
        report = self.env.ref('ocs_weight_master.action_report_weighbridge_transaction')
        url = f'/report/html/{report.report_name}/{self.id}'
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new',
        }

