from odoo import models, fields, api


class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real Estate Property'

    name = fields.Char(string='Property Name', required=True)
    property_type = fields.Selection([
        ('building', 'Building'),
        ('apartment', 'Apartment Complex'),
        ('villa', 'Villa'),
        ('commercial', 'Commercial Property'),
    ], string='Property Type', required=True)
    address = fields.Text(string='Full Address')
    city = fields.Char(string='City')
    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country')
    zip = fields.Char(string='ZIP Code')
    active = fields.Boolean(string='Active', default=True)
    image = fields.Binary(string='Image')
    unit_count = fields.Integer(string='Units', compute='_compute_unit_count')
    note = fields.Text(string='Internal Notes')


    """Computes and stores the count of units (estate.unit) linked to the current property (property_id)."""
    def _compute_unit_count(self):
        for record in self:
            record.unit_count = self.env['estate.unit'].search_count([('property_id', '=', record.id)])


    """Opens a list view of all units (estate.unit) associated with the current property, 
    allowing navigation to detailed forms."""
    def action_view_units(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Property Units',
            'res_model': 'estate.unit',
            'domain': [('property_id', '=', self.id)],
            'view_mode': 'list,form',
            'context': {'default_property_id': self.id},
        }