from odoo import models, fields, api
from datetime import datetime

class WeighbridgeTransaction(models.Model):
    _name = "weighbridge.transaction"
    _description = "Weighbridge Transaction"
    _order = "create_date desc, id desc"
    _rec_name = "voucher_no"

    voucher_no = fields.Char(string="Voucher No", required=True, readonly=True, copy=False, default='New')
    vehicle_no = fields.Char(string="Vehicle No", required=True)
    
    # Driver - Many2one relationship
    driver_id = fields.Many2one('weighbridge.driver', string="Driver", help="Select driver")
    
    # Driver fields (can be filled from driver_id or entered manually)
    driver_name = fields.Char(string="Driver Name")
    driver_nrc = fields.Char(string="NRC")
    driver_phone = fields.Char(string="Phone Number")
    
    # Company/Customer
    company_name = fields.Char(string="Company Name")
    partner_id = fields.Many2one('res.partner', string="Customer", help="Select customer")
    
    # Responsible Employee
    responsible_id = fields.Many2one('hr.employee', string="Responsible", help="Select employee")
    
    deliver_to = fields.Text(string="Deliver To")
    
    # Transaction Type - Many2one relationship
    # Note: required=False initially to avoid initialization issues, validation in create()
    type_id = fields.Many2one('weighbridge.transaction.type', string="Type", required=False)
    
    # Keep type as Selection for backward compatibility during migration
    # Will be synced with type_id via onchange
    type = fields.Selection([
        ('in', 'In'),
        ('out', 'Out'),
        ('in_out', 'In-Out'),
        ('visit', 'Visit')
    ], string="Type Code", required=False)
    
    @api.model
    def _default_type_id(self):
        """Default to 'In' type - safe to call after model initialization"""
        try:
            type_record = self.env['weighbridge.transaction.type'].search([('code', '=', 'in')], limit=1)
            if not type_record:
                # Fallback: return first active type if 'in' doesn't exist
                type_record = self.env['weighbridge.transaction.type'].search([('active', '=', True)], limit=1)
            return type_record.id if type_record else False
        except Exception:
            # During module installation, table might not exist yet
            return False
    
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

    @api.onchange('driver_id')
    def _onchange_driver_id(self):
        """Update driver fields when driver is selected"""
        if self.driver_id:
            self.driver_name = self.driver_id.name
            self.driver_nrc = self.driver_id.nrc
            self.driver_phone = self.driver_id.phone
        else:
            # Clear fields if driver is removed
            self.driver_name = False
            self.driver_nrc = False
            self.driver_phone = False

    @api.onchange('type_id')
    def _onchange_type_id(self):
        """Sync type field when type_id is selected"""
        if self.type_id:
            self.type = self.type_id.code

    @api.onchange('type')
    def _onchange_type(self):
        """Sync type_id when type is selected"""
        if self.type:
            type_record = self.env['weighbridge.transaction.type'].search([('code', '=', self.type)], limit=1)
            if type_record:
                self.type_id = type_record

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate voucher numbers and set default type"""
        for vals in vals_list:
            if vals.get('voucher_no', 'New') == 'New':
                # Generate voucher number: YYYYMMDDHHMMSS (datetime only)
                now = datetime.now()
                vals['voucher_no'] = now.strftime('%Y%m%d%H%M%S')
            
            # Set default type_id if not provided (required field)
            if not vals.get('type_id'):
                try:
                    # Try to get default type from context first
                    if self.env.context.get('default_type_id'):
                        vals['type_id'] = self.env.context.get('default_type_id')
                    else:
                        # Try XML ID reference first (fastest, no DB query)
                        try:
                            type_ref = self.env.ref('ocs_weight_master.transaction_type_in', raise_if_not_found=False)
                            if type_ref:
                                vals['type_id'] = type_ref.id
                        except Exception:
                            pass
                        
                        # Fallback to search method
                        if not vals.get('type_id'):
                            default_type_id = self._default_type_id()
                            if default_type_id:
                                vals['type_id'] = default_type_id
                except Exception:
                    # If all else fails, try to get any active type
                    try:
                        any_type = self.env['weighbridge.transaction.type'].search([('active', '=', True)], limit=1)
                        if any_type:
                            vals['type_id'] = any_type.id
                    except Exception:
                        pass
            
            # Ensure type_id is set (required field validation)
            if not vals.get('type_id'):
                raise ValueError("Transaction type is required. Please select a type.")
            
            # Sync type field with type_id
            if vals.get('type_id') and not vals.get('type'):
                try:
                    type_record = self.env['weighbridge.transaction.type'].browse(vals['type_id'])
                    if type_record.exists():
                        vals['type'] = type_record.code
                except Exception:
                    pass
            
            # Sync type_id with type field (if type is provided but type_id is not)
            if vals.get('type') and not vals.get('type_id'):
                try:
                    type_record = self.env['weighbridge.transaction.type'].search([('code', '=', vals['type'])], limit=1)
                    if type_record:
                        vals['type_id'] = type_record.id
                except Exception:
                    pass
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

