# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
	'name': 'Assets',
	'version': '1.1',
	'author': 'Bassam Infotech',
	'category': 'General',
	'website': 'https://www.bassaminfotech.com',
	'depends': ['base','account','account_asset','product','school','school_fees','stock'],
	'data': [   			
			'views/asset_management.xml',
		    'views/ir_sequence.xml'
			],

	'demo': [],
	'installable': True,
	'auto_install': False,
}