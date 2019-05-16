# -*- coding: utf-8 -*-
{

    'name': 'Queue Management',
    'description': "Queue Management",
    'version': '1.0.1',
    'author': 'Bassam Infotech',
    'website': 'http://www.bassaminfotech.com',
    'license': 'AGPL-3',
    'depends': ['base','school'],
    'data': [
        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/queue_management_view.xml',
        'views/queue_management.xml',
        # 'report/token_view.xml',
        'report/token_management_report.xml',
    ]
}