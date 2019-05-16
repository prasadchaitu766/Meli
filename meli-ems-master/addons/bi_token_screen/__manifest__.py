# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
# Please see LICENSE file.
#################################################################################

{
    'name': 'Token screen',
    'version': '1.0',
    'category': 'Students',
    'website': 'http://www.bassaminfotech.com',
    'summary': "",
    'description': "",
    'author': "Bassaminfotech LLP",
    'website': "www.bassaminfotech.com",
    'depends': ['bi_queue_management'],
    'data': [  
            # 'security/ir.model.access.csv',     
            'views/bi_token_screen_template.xml',        
    ],
    # 'qweb': ['static/src/xml/bi_student_screen.xml',],
    'images': ['static/description/customer_screen.png'],
    'installable': True,
    'auto_install': False
}

