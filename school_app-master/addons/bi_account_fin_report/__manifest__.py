# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account Report',
    'version': '1.0',
    'category': 'General',
    'sequence': 15,
    'summary': 'It contans accounts information',
    'description': """ """,
    'website': 'http://www.bassaminfotech.com',
    'depends': ['base','account'],
    'data': [   
    
              'views/account_journal_views.xml',
              

    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
