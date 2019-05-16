# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'School Security',
	'version': '1.1',
	'category': 'School',
	'author': 'Bassam Infotech LLP',
	'website': 'http://www.bassaminfotech.com/',
	'depends': ['base','school','bi_employee_advance','bi_hr','hr_resignation','bi_material_request_form','hr_loan','website_support','exam_test_quiz','bi_asset_management','oh_appraisal','bi_queue_management','account_budget','web_widget_image_webcam','bi_account_balance','bi_account_journal','bi_account_voucher','bi_campus_screen','bi_employee_card','bi_invoicepayment','bi_ledger_report','bi_mobile_api','bi_student_screen','bi_token_screen','bi_vacancy_screen','gts_coa_hierarchy_v10','export_employee_information','web_widget_timepicker'],
	'data': [
			'security/security.xml', 'security/ir.model.access.csv',
		   ],

	'demo': [],
	'installable': True,
	'auto_install': False,
}