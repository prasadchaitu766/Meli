# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'SqlConnector',
    'version': '1.0',
    'category': 'General',
    'sequence': 15,
    'summary': 'MS sql connector',
    'description': """    """,
    'website': 'http://www.bassaminfotech.com',
    'depends': ['base','hr','hr_attendance'],
    'data': [   
        'security/security_view.xml',
        'views/sqlconnector_view.xml',        
        'security/ir.model.access.csv'
        ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
