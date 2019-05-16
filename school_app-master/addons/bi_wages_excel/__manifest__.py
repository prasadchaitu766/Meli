# -*- coding: utf-8 -*-
{

    'name': 'Wage Report',
    'description': "Wage Report Excel",
    'version': '1.0.1',
    'author': 'Bassam Infotech',
    'website': 'http://www.bassaminfotech.com',
    'license': 'AGPL-3',
    'depends': ['report_xlsx','hr_payroll','l10n_in_hr_payroll'],
    'data': [
        
        "report/payslip_wages.xml",
        'wizard/wages_wizard.xml',
        
    ]
}
