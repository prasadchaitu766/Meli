# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Advance report',
    'version': '1.1',
    'author': 'Bassam Infotech',
    'category': 'Advance Details',
    'website': 'https://www.bassaminfotech.com',

    'depends': ['base','hr','bi_employee_advance'],
    'data': [
            'report/advance_report.xml',
            'report/advance_report_view.xml',
            ],

    'demo': [],
    'installable': True,
    'auto_install': False,
}