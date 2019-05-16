# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Devintelle Software Solutions (<http://www.devintellecs.com>).
#
##############################################################################

{
    'name' : 'Employee Profile Report',
	'version' : '1.0',
	'category': 'hr',
    'sequence':1,
    'summary': 'Employee profile report',
	'description' : """Print Reports about employee's details""",
	'author' : 'DevIntelle Consulting Services Pvt.',
	'website' : 'https://www.devintellecs.com',
	'images': ['images/main_screenshot.png'],
	'depends' : ['report','hr'],
	'data' : [
				'report/dev_emp_profile_report_template.xml',
				'report/dev_emp_profile_report_call.xml',
		],	
	'demo' : [],
	'test' : [],
    'qweb' : [],
    'installable' : True,
	'auto_install' : False,	
	'application' : True,
    	
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:



	
