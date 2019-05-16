# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Petty Cash Management',
    'version': '1.1',
    'category': 'Accounting',
     'author': 'Bassam Infotech LLP',
    'website': 'http://www.bassaminfotech.com/',

    'depends': ['base','account','account_voucher','school'],
    'data': [ 
              'security/petty_cash_security.xml',
              'security/ir.model.access.csv',
              'views/account_petty_cash_view.xml',
              'views/account_journal_form_view.xml',
              'data/ir_sequence_data.xml',

    		 ],

    'demo': [],
    'installable': True,
    'auto_install': False,
}
