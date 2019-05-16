# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee',
    'version': '1.0',
    'category': 'General',
    'sequence': 15,
    'summary': 'Employee Salary Details',
    'description': """    """,
    'website': 'http://www.bassaminfotech.com',
    'depends': ['base','hr','hr_payroll','bi_hr'],
    'data': [   
        'security/security.xml',
        'views/employee_salary.xml',
        'security/ir.model.access.csv',
        'views/ir_sequence.xml'
    ],
    'demo': [],
    'css': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
