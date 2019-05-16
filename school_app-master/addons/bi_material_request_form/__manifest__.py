# -*- coding: utf-8 -*-

{
    'name': 'Material Request Form',
    'summary': 'Material request From for Internal Transfer',
    'version': '1.0',
    'author': 'Bassam Infotech LLP',
    "license": "LGPL-3",
    'depends': ['base','product','stock','school','bi_hr','purchase_requisition','bi_asset_management','hr'],
    'data': [  
                'security/security.xml',
                'security/ir.model.access.csv',
                'views/ir_sequence.xml',
                'views/bi_material_request_delivery_slip.xml',
                'views/material_request.xml',
                'report/report.xml',
                'report/material_request_template.xml'             
    		 ],

    'demo': [],
    'installable': True,
    'auto_install': False,
}
