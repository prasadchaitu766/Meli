# -*- coding: utf-8 -*-
{

    'name': 'Mustroll Report',
    'description': "Mustroll Report Excel",
    'version': '1.0.1',
    'author': 'Bassam Infotech',
    'website': 'http://www.bassaminfotech.com',
    'license': 'AGPL-3',
    'depends': ['report_xlsx','hr_payroll','l10n_in_hr_payroll'],
    'data': [
        'security/ir.model.access.csv',
        "report/bi_mustroll.xml",
        'wizard/bi_mustroll_excel.xml',
        
    ]
}
