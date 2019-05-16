# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError


class ConcessionReason(models.TransientModel):
		_name = "concession.reason"

		concession_reason = fields.Text(string='Reason')

		@api.multi
		def save_concession(self):
				self.env['student.payslip'
								 ].browse(self._context.get('active_id')
													).write({'concession_reason':self.concession_reason,'state':'submit_discount'})
				return True
