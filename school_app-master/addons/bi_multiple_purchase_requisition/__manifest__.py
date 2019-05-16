{
    'name': 'Purchase order for multiple Purchase Requisition',
    'category': 'Generic Modules/Others',
    'license': 'AGPL-3',
    'author': 'Bassam Infotech LLP',
    'website': 'http://www.bassaminfotech.com/',
    'depends': ['purchase','purchase_requisition'], 
    'init_xml': [],
    'data': [ 
        'security/ir.model.access.csv',
        'wizard/purchase_order.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
}

