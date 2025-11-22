from odoo import models, fields, api

class Driver(models.Model):
    _name = "weighbridge.driver"
    _description = "Weighbridge Driver"
    _order = "name"
    _rec_name = "name"

    name = fields.Char(string="Driver Name", required=True)
    nrc = fields.Char(string="NRC", help="National Registration Card Number")
    phone = fields.Char(string="Phone Number")
    email = fields.Char(string="Email")
    address = fields.Text(string="Address")
    
    # Link to partner if driver is also a contact
    partner_id = fields.Many2one('res.partner', string="Related Contact", 
                                 help="Link to contact if driver exists in contacts")
    
    # Additional fields
    license_no = fields.Char(string="License Number")
    license_expiry = fields.Date(string="License Expiry Date")
    notes = fields.Text(string="Notes")
    
    # Transaction count (computed)
    transaction_count = fields.Integer(string="Transaction Count", compute="_compute_transaction_count")
    
    @api.depends('name')
    def _compute_transaction_count(self):
        """Count transactions for this driver"""
        for driver in self:
            driver.transaction_count = self.env['weighbridge.transaction'].search_count([
                ('driver_id', '=', driver.id)
            ])

