# -*- coding: utf-8 -*-
{

    'name': 'Employee Ledger Report',
    'description': "Employee Ledger Report Excel",
    'version': '1.0.1',
    'author': 'Bassam Infotech',
    'website': 'http://www.bassaminfotech.com',
    'license': 'AGPL-3',
    'depends': ['report_xlsx','hr_payroll','l10n_in_hr_payroll'],
    'data': [
        
        'report/bi_employee_ledger.xml',
        'wizard/bi_ledger_wizard.xml',
        
    ]
}
