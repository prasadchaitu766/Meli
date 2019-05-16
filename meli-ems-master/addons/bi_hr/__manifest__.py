# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'MELI',
    'version': '1.1',
    'author': 'Bassam Infotech',
    'category': 'Hr',
    'website': 'https://www.bassaminfotech.com',

    'depends': ['base','l10n_in_hr_payroll','hr_contract','report_xlsx','hr_payroll','hr_holidays','hr_attendance','sale_timesheet','hr_recruitment','hr_recruitment_survey','hr_expense','school','resource','bi_mustroll_excel','bi_sqlconnector','dev_employee_profile','hr_public_holidays','oh_employee_documents_expiry','mail','hr_payroll_account'],
    'data': [
            'security/security_view.xml',
            'views/payslip_view.xml',
            'views/payslip_ctc_view.xml',
            # 'views/employee_ledger_view.xml',
            'views/sale_incentive_view.xml',
            # 'views/employee_norms_view.xml',
            'views/survey_changes.xml',
            'views/payslip_survey_question_view.xml',
            'views/bi_employee_menuitem.xml',
            # 'views/employee_views.xml',
            'security/ir.model.access.csv',
            'report/hr_payroll_report.xml',
            'report/report_payslip_templates.xml',
            'report/hr_payroll_run_report.xml',
            'report/print_report_excel_view.xml',
            'report/hr_payment_advice.xml',
            'wizard/hr_payroll_contribution_register_report_views.xml',
            'wizard/hr_employee_list.xml',
            'report/employee_list.xml',
            'data/ir_sequence_data.xml',
            'report/report.xml',
            'report/contract_report_template.xml'
            ],

    'demo': [],
    'installable': True,
    'auto_install': False,
}