# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account_Journal',
    'version': '1.0',
    'category': 'General',
    'sequence': 15,
    'summary': 'It contans accounts information',
    'description': """ """,
    'website': 'http://www.bassaminfotech.com',
    'depends': ['base','account','school'],
    'data': [   
    
              'views/account_journal_views.xml',
              'views/multi_account_journal_views.xml',
              'views/ir_sequence.xml',
              'views/account_journal_voucher.xml',
              'security/ir.model.access.csv',
              'report/account_template.xml',
              'report/account_report.xml',
              'report/account_journal_report.xml',
              'report/account_voucher_report.xml',
              'report/account_draft_template.xml',
              'report/account_voucher_draft_report.xml'

    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
