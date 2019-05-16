# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'School',
    'version': '10.0.1.0.13',
    'author': '''Bassam Infotech LLP''',
    'website': 'http://www.bassaminfotech.com',
    'category': 'School Management',
    'license': "AGPL-3",
    'complexity': 'easy',
    'Summary': 'A Module For School Management',
    'images': ['static/description/EMS.jpg'],


    'depends': ['base','hr', 'report','hr_expense', 'account', 'account_accountant','purchase','sale','stock','procurement','contacts','account_asset'],
    'data': ['security/school_security.xml',
             'security/campus_security.xml',
             'security/ir.model.access.csv',
             'wizard/terminate_reason_view.xml',
             'wizard/followup_list_view.xml',
             'wizard/wiz_send_email_view.xml',
             'views/student_view.xml',
             'views/school_view.xml',
             'views/request_form_views.xml',
             'views/teacher_view.xml',
             'views/purchase_view.xml',
             'views/warning_view.xml',
             'views/sale_view.xml',
             'views/stock_view.xml',
             'views/parent_view.xml',
             'views/account_view.xml',
             'data/student_sequence.xml',
             'wizard/assign_roll_no_wizard.xml',
             'wizard/move_standards_view.xml',
             'views/report_view.xml',
             'views/identity_card.xml',
             'views/users_view.xml',
             'views/template_view.xml'],
    'demo': ['demo/school_demo.xml'],
    'installable': True,
    'application': True
}
