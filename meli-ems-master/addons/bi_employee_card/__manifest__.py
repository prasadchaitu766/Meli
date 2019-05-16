# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Employee Id Card',
    'version': '1.1',
    'author': 'Bassam Infotech',
    'category': 'Hr',
    'website': 'https://www.bassaminfotech.com',

    'depends': ['base','hr_payroll','hr_holidays','hr_attendance','school'],
    'data': [
            'report/hr_employee_badge.xml',
            'report/student_badge.xml',
            'report/teacher_badge.xml',
            ],
    'css': ['static/src/css/badge.css'],
    'demo': [],
    'installable': True,
    'auto_install': False,
}