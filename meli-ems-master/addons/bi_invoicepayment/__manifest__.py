# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Multiple Invoice Payment',
    'version': '1.1',
    'category': 'Accounting',
     'author': 'Bassam Infotech LLP',
    'website': 'http://www.bassaminfotech.com/',

    'depends': ['base','account','school'],
    'data': ['security/security.xml',
             'views/paymentinvoice_view.xml',
             'views/paymentinvoicesupplier_view.xml',
             'security/ir.model.access.csv',
             'report/payment_invoice_report.xml',
             'report/payment_report.xml'
            ],

    'demo': [],
    'installable': True,
    'auto_install': False,
}
