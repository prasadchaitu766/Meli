# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

{
    'name': "Online Exam",
    'version': "1.0.2",
    'author': "Bassam Infotech LLP",
    'category': "Tools",
    'support': "mhmmdfaizal@outlook.com",
    'summary': "Multi Purpose Online Examination Module",
    'license': "AGPL-3",
    'complexity': 'easy',
    'depends': ['website','mail','contacts','school','exam'],
    'data': [
        'data/mail.template.csv',
        'data/res.groups.csv',
        'security/ir.model.access.csv',
        'views/etq_exam.xml',
        'views/exam_templates.xml',
        'views/etq_results.xml',
        'views/etq_exam_share.xml',
        'views/exam.xml',
        'report/exam_test_view.xml',
        'report/exam_report_certificate.xml',
    ],
    'demo': [],
    'images':[
    'static/description/2.jpg',
    ],
    'installable': True,
}
