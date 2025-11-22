from odoo import models, fields, api

class TransactionType(models.Model):
    _name = "weighbridge.transaction.type"
    _description = "Weighbridge Transaction Type"
    _order = "sequence, name"
    _rec_name = "name"

    name = fields.Char(string="Type Name", required=True)
    code = fields.Char(string="Code", required=True, help="Internal code (e.g., 'in', 'out', 'in_out', 'visit')")
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10, help="Order in which types appear")
    active = fields.Boolean(string="Active", default=True)
    
    # Transaction count (computed)
    transaction_count = fields.Integer(string="Transaction Count", compute="_compute_transaction_count")
    
    @api.depends('code')
    def _compute_transaction_count(self):
        """Count transactions for this type"""
        for trans_type in self:
            trans_type.transaction_count = self.env['weighbridge.transaction'].search_count([
                ('type', '=', trans_type.code)
            ])

