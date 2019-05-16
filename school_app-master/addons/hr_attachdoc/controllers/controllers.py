# -*- coding: utf-8 -*-
from odoo import http

# class HrAttachdoc(http.Controller):
#     @http.route('/hr_attachdoc/hr_attachdoc/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_attachdoc/hr_attachdoc/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_attachdoc.listing', {
#             'root': '/hr_attachdoc/hr_attachdoc',
#             'objects': http.request.env['hr_attachdoc.hr_attachdoc'].search([]),
#         })

#     @http.route('/hr_attachdoc/hr_attachdoc/objects/<model("hr_attachdoc.hr_attachdoc"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_attachdoc.object', {
#             'object': obj
#         })