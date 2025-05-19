from odoo import models, fields, api


class EstateTenant(models.Model):
    _name = 'estate.tenant'
    _description = 'Property Tenant'


    name = fields.Char(string='Tenant Name', required=True)
    is_company = fields.Boolean(string='Is a Company')
    company_name = fields.Char(string='Company Name')
    contact_person = fields.Char(string='Contact Person')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    mobile = fields.Char(string='Mobile')
    address = fields.Text(string='Address')
    id_type = fields.Selection([
        ('passport', 'Passport'),
        ('id_card', 'National ID'),
        ('driver_license', 'Driver License'),
    ], string='ID Type')
    id_number = fields.Char(string='ID Number')
    lease_ids = fields.One2many('estate.lease', 'tenant_id', string='Lease History')
    active = fields.Boolean(string='Active', default=True)


    """Resets company_name when marking as a company or contact_person when unmarking"""
    @api.onchange('is_company')
    def _onchange_is_company(self):
        if self.is_company:
            self.company_name = False
        else:
            self.contact_person = False