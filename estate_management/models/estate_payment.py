from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EstatePayment(models.Model):
    _name = 'estate.payment'
    _description = 'Rent Payment'

    lease_id = fields.Many2one(
        'estate.lease',
        string='Lease',
        required=True,
        default=lambda self: self.env.context.get('default_lease_id'))
    name = fields.Char(string='Reference',related='lease_id.name', required=True, copy=False, readonly=True,)
    tenant_id = fields.Many2one('estate.tenant', string='Tenant', related='lease_id.tenant_id', store=True)
    unit_id = fields.Many2one('estate.unit', string='Unit', related='lease_id.unit_id', store=True)
    amount = fields.Float(string='Amount', required=True)
    due_date = fields.Date(string='Due Date', required=True)
    payment_date = fields.Date(string='Payment Date')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', tracking=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('check', 'Check'),
        ('online', 'Online Payment'),
    ], string='Payment Method')
    reference = fields.Char(string='Payment Reference')

    # Button visibility fields (computed)
    show_paid_btn = fields.Boolean(compute='_compute_button_visibility')
    show_overdue_btn = fields.Boolean(compute='_compute_button_visibility')
    show_cancel_btn = fields.Boolean(compute='_compute_button_visibility')

    """Computes the visibility of action buttons based on the current record state."""
    @api.depends('state')
    def _compute_button_visibility(self):
        for rec in self:
            is_pending = rec.state == 'pending'
            rec.show_paid_btn = is_pending
            rec.show_overdue_btn = is_pending
            rec.show_cancel_btn = is_pending


    """ Marks pending payments as paid with today's date (raises error if not pending)."""
    def action_mark_paid(self):
        for payment in self:
            if payment.state != 'pending':
                raise ValidationError("Only pending payments can be marked as paid!")
            payment.write({
                'state': 'paid',
                'payment_date': fields.Date.today(),
            })


    """Automatically flags pending payments as overdue if past their due date."""
    def action_mark_overdue(self):
        for payment in self:
            if payment.state != 'pending':
                continue
            if fields.Date.today() > payment.due_date:
                payment.write({
                    'state': 'overdue',
                })


    """Cancels non-paid payments (blocks cancellation if already paid)."""
    def action_cancel_payment(self):
        for payment in self:
            if payment.state == 'paid':
                raise ValidationError("You cannot cancel a paid payment!")
            payment.write({
                'state': 'cancelled',
            })


    """Scheduled task that checks and updates pending payments to overdue if expired."""
    @api.model
    def _cron_check_overdue_payments(self):
        payments = self.search([
            ('state', '=', 'pending'),
            ('due_date', '<', fields.Date.today()),
        ])
        payments.action_mark_overdue()