from odoo import models, fields, api


class EstateUnit(models.Model):
    _name = 'estate.unit'
    _description = 'Property Unit'

    name = fields.Char(string='Unit Number/Name', required=True)
    property_id = fields.Many2one('estate.property', string='Property', required=True)
    unit_type = fields.Selection([
        ('studio', 'Studio'),
        ('1bed', '1 Bedroom'),
        ('2bed', '2 Bedroom'),
        ('3bed', '3 Bedroom'),
        ('penthouse', 'Penthouse'),
        ('office', 'Office'),
        ('retail', 'Retail Space'),
    ], string='Unit Type', required=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('rented', 'Rented'),
        ('maintenance', 'Under Maintenance'),
    ], string='Status', default='available')
    area = fields.Float(string='Area (sqm)')
    bedrooms = fields.Integer(string='Bedrooms')
    bathrooms = fields.Integer(string='Bathrooms')
    amenities = fields.Text(string='Amenities')
    current_lease_id = fields.Many2one('estate.lease', string='Current Lease', compute='_compute_current_lease')
    active = fields.Boolean(string='Active', default=True)


    """Sets the unit's active lease by searching for an 'active' lease linked to the unit."""
    def _compute_current_lease(self):
        for unit in self:
            lease = self.env['estate.lease'].search([
                ('unit_id', '=', unit.id),
                ('state', '=', 'active'),
            ], limit=1)
            unit.current_lease_id = lease.id if lease else False


    """Shows a warning if unit is marked 'rented' without an active lease."""
    @api.onchange('status')
    def _onchange_status(self):
        if self.status == 'rented' and not self.current_lease_id:
            return {
                'warning': {
                    'title': 'Warning',
                    'message': 'This unit is marked as rented but has no active lease!',
                }
            }