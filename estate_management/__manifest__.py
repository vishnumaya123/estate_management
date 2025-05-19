{
    'name': 'Estate Management',
    'version': "18.0.1.0.0",
    'summary': 'Estate Management System',
    'description': """
        Comprehensive solution for managing properties, tenants, leases, and payments
        in a real estate/property management company.
    """,
    'author': 'Vishnumaya E M',
    'category': 'Real Estate',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/estate_data.xml',
        'data/estate_demo_data.xml',
        'views/estate_lease_views.xml',
        'views/estate_property_views.xml',
        'views/estate_unit_views.xml',
        'views/estate_tenant_views.xml',
        'views/estate_payment_views.xml',
        'views/estate_maintenance_views.xml',
        'views/estate_menus.xml',
    ],
    'installable': True,
    'application': True,
}
