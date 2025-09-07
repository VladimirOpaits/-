{
    'name': 'Workplace ARM',
    'version': '4.0',
    'category': 'Manufacturing',
    'summary': 'Workplace management and ARM integration',
    'description': """
        This module provides workplace management functionality with ARM integration.
        Features include:
        - Workplace management
        - ARM integration
        - Manufacturing support
    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'web', 'mrp', 'maintenance'],
    'data': [
        'security/ir.model.access.csv',
        'views/workplace_views.xml',
        'views/workplace_task_views.xml',
        'views/menu_views.xml',
        'data/wizard_views.xml',
        'data/demo_data.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}