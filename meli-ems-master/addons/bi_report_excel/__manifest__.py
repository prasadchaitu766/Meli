# -*- coding: utf-8 -*-
{

    'name': 'Payslip Report Excel',
    'description': "Goods & Service-Tax.",
    'version': '1.0.1',
    'author': 'Merlin Tecsol Pvt. Ltd.',
    'website': 'http://www.merlintecsol.com',
    'license': 'AGPL-3',
    'depends': ['report_xlsx','hr_payroll','l10n_in_hr_payroll'],
    'data': [
        
        "report/bi_payslip.xml",
        'wizard/bi_payslip_excel.xml',
        
    ]
}
