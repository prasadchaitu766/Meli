# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Fees Management',
    'version': "10.0.1.0.4",
    'author': '''Serpent Consulting Services Pvt. Ltd.''',
    'website': 'http://www.serpentcs.com',
    'category': 'School Management',
    'license': "AGPL-3",
    'complexity': 'easy',
    'summary': 'A Module For Fees Management In School',
    'depends': ['account', 'account_accountant', 'school','mail'],
    'images': ['static/description/SchoolFees.png'],
    'data': ['security/ir.model.access.csv',
             'security/security_fees.xml',
             'wizard/concession_view.xml',
             'wizard/school_fee_wizard.xml',
             'views/bi_report_invoice_student.xml',
             'report/fees_report.xml',
             'report/fees_report_view.xml',
             'views/school_fees_view.xml',
             'views/school_fees_sequence.xml',
             'views/student_payslip.xml',
             'views/student_fees_register.xml',
             'views/report_view.xml',
             'data/student_sequence.xml',
             'data/invoice_action_data.xml'
             ],
    'demo': ['demo/school_fees_demo.xml'],
    'installable': True,
    'application': True
}
