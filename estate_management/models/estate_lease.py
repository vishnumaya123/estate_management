from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class EstateLease(models.Model):
    _name = 'estate.lease'
    _description = 'Lease Contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Lease Reference', required=True, copy=False,)
    tenant_id = fields.Many2one('estate.tenant', string='Tenant', required=True)
    unit_id = fields.Many2one('estate.unit', string='Unit', required=True)
    property_id = fields.Many2one('estate.property', string='Property', related='unit_id.property_id', store=True)
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    monthly_rent = fields.Float(string='Monthly Rent', required=True)
    deposit = fields.Float(string='Security Deposit')
    payment_term = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], string='Payment Term', default='monthly', required=True)
    payment_day = fields.Integer(string='Payment Day of Month', default=1, help='Day of each month on which rent payment is due.')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('renewed', 'Renewed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    payment_ids = fields.One2many('estate.payment', 'lease_id', string='Payments')
    notes = fields.Text(string='Terms & Conditions')

    # Button visibility fields (computed)
    show_confirm_btn = fields.Boolean(compute='_compute_button_visibility')
    show_expire_btn = fields.Boolean(compute='_compute_button_visibility')
    show_renew_btn = fields.Boolean(compute='_compute_button_visibility')
    show_cancel_btn = fields.Boolean(compute='_compute_button_visibility')

    """Computes the visibility of action buttons based on the current lease state."""
    @api.depends('state')
    def _compute_button_visibility(self):
        for rec in self:
            rec.show_confirm_btn = rec.state == 'draft'
            rec.show_expire_btn = rec.state == 'confirmed'
            rec.show_renew_btn = rec.state == 'expired'
            rec.show_cancel_btn = rec.state in ['draft', 'confirmed']


    """Validates that the lease end date is after the start date."""
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for lease in self:
            if lease.start_date >= lease.end_date:
                raise ValidationError("End date must be after start date!")


    """Confirms the lease by activating it, updating the unit status to "rented", 
    and scheduling payment records."""
    def action_confirm(self):
        for lease in self:
            if lease.unit_id.status != 'available':
                raise ValidationError("This unit is not available for lease!")

            lease.write({
                'state': 'active',
            })
            lease.unit_id.write({
                'status': 'rented',
            })

            # Schedule payments
            lease._schedule_payments()


    """Automatically generates payment records based on the lease term and payment frequency."""
    def _schedule_payments(self):
        self.ensure_one()
        Payment = self.env['estate.payment']

        start_date = self.start_date
        end_date = self.end_date

        if self.payment_term == 'monthly':
            delta = timedelta(days=30)
        elif self.payment_term == 'quarterly':
            delta = timedelta(days=90)
        elif self.payment_term == 'yearly':
            delta = timedelta(days=365)

        current_date = start_date
        while current_date < end_date:
            due_date = current_date.replace(day=self.payment_day)
            if due_date < current_date:
                due_date = (current_date + timedelta(days=32)).replace(day=self.payment_day)

            Payment.create({
                'lease_id': self.id,
                'amount': self.monthly_rent * (
                    3 if self.payment_term == 'quarterly' else 12 if self.payment_term == 'yearly' else 1),
                'due_date': due_date,
                'state': 'pending',
            })

            current_date = current_date + delta


    """Wizard form to create a new lease contract with pre-filled details from the current lease
     for easy renewal."""
    def action_renew(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Renew Lease',
            'res_model': 'estate.lease',
            'view_mode': 'form',
            'context': {
                'default_tenant_id': self.tenant_id.id,
                'default_unit_id': self.unit_id.id,
                'default_previous_lease_id': self.id,
            },
            'target': 'new',
        }


    """Expires the lease and updates the unit status to "available"."""
    def action_expire(self):
        for lease in self:
            lease.write({
                'state': 'expired',
            })
            lease.unit_id.write({
                'status': 'available',
            })


    """Cancels the lease, marks the unit as "available", and cancels all pending payments."""
    def action_cancel(self):
        for lease in self:
            lease.write({
                'state': 'cancelled',
            })
            lease.unit_id.write({
                'status': 'available',
            })
            lease.payment_ids.filtered(lambda p: p.state == 'pending').write({'state': 'cancelled'})


    """Scheduled method that creates reminder activities for leases expiring within the next 30 days."""
    def _cron_check_lease_expiry(self):
        leases = self.search([
            ('state', '=', 'active'),
            ('end_date', '<=', fields.Date.today() + timedelta(days=30)),
        ])

        activity_type = self.env.ref('estate_management.mail_act_lease_expiry', raise_if_not_found=False)
        if not activity_type:
            # Fallback if activity type doesn't exist
            return

        for lease in leases:
            # Check if notification already exists
            existing_activity = self.env['mail.activity'].search([
                ('res_id', '=', lease.id),
                ('res_model', '=', 'estate.lease'),
                ('activity_type_id', '=', activity_type.id),
                ('date_deadline', '>=', fields.Date.today()),
            ], limit=1)

            if not existing_activity:
                lease.activity_schedule(
                    activity_type.xml_id,
                    user_id=lease.property_id.responsible_id.id or self.env.uid,
                    note=f"Lease {lease.name} is expiring on {lease.end_date}.",
                    date_deadline=lease.end_date - timedelta(days=7))