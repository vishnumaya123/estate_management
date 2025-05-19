from odoo import models, fields, api


class EstateMaintenance(models.Model):
    _name = 'estate.maintenance'
    _description = 'Maintenance Request'


    name = fields.Char(string='Reference', required=True, copy=False,)
    lease_id = fields.Many2one('estate.lease', string='Lease')
    tenant_id = fields.Many2one('estate.tenant', string='Tenant', related='lease_id.tenant_id', store=True)
    unit_id = fields.Many2one('estate.unit', string='Unit', required=True)
    property_id = fields.Many2one('estate.property', string='Property', related='unit_id.property_id', store=True)
    request_date = fields.Date(string='Request Date', default=fields.Date.today())
    completion_date = fields.Date(string='Completion Date')
    description = fields.Text(string='Description', required=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority', default='medium')
    state = fields.Selection([
        ('new', 'New'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='new', tracking=True)
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    cost = fields.Float(string='Estimated Cost')
    actual_cost = fields.Float(string='Actual Cost')
    notes = fields.Text(string='Notes')

    # Button visibility fields (computed)
    show_assign_btn = fields.Boolean(compute='_compute_button_visibility')
    show_start_btn = fields.Boolean(compute='_compute_button_visibility')
    show_complete_btn = fields.Boolean(compute='_compute_button_visibility')
    show_cancel_btn = fields.Boolean(compute='_compute_button_visibility')


    """Computes the visibility of action buttons based on the current record state."""
    @api.depends('state')
    def _compute_button_visibility(self):
        for rec in self:
            rec.show_assign_btn = rec.state == 'new'
            rec.show_start_btn = rec.state == 'assigned'
            rec.show_complete_btn = rec.state == 'in_progress'
            rec.show_cancel_btn = rec.state not in ('completed', 'cancelled')

    """Updates the record's state to 'assigned'."""
    def action_assign(self):
        for request in self:
            request.write({
                'state': 'assigned',
            })


    """Updates the record's state to 'in_progress'."""
    def action_start(self):
        for request in self:
            request.write({
                'state': 'in_progress',
            })


    """Marks the record as 'completed' and sets the completion date."""
    def action_complete(self):
        for request in self:
            request.write({
                'state': 'completed',
                'completion_date': fields.Date.today(),
            })


    """Updates the record's state to 'cancelled'."""
    def action_cancel(self):
        for request in self:
            request.write({
                'state': 'cancelled',
            })