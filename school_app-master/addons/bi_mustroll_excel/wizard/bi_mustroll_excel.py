# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class WizardBiMustroll(models.TransientModel):
	_name = 'bi.mustroll'

	# start_date = fields.Date('From Date',default=fields.Datetime.now(), required=True)
	# end_date = fields.Date('To Date',default=fields.Datetime.now(),required=True)
	start_date = fields.Datetime(required=True)
	end_date = fields.Datetime(required=True)
	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
	# mustroll_ids = fields.Many2many('hr.payslip.run', 'bi_mustroll_excel_rel', 'mustroll_id', 'conf_id', string="Mustroll", copy=False, readonly=False)

	# @api.multi
	# def print_Excel_report(self,vals):
	# 	active_ids = self.env.context.get('active_ids', [])
	# 	# raise UserError(_(str(active_ids)))
	# 	datas = {
	# 		 'ids': active_ids,
	# 		 'model': 'hr.attendance',
	# 		 'form': self.read()[0]
	# 	}
	# 	return self.env["report"].get_action(self, 'account.bi.mustroll.xlsx', data=datas)

	@api.multi
	def print_Excel_report(self,vals):
		invoice_obj = self.env['check.date'].search([])
		if invoice_obj:
			invoice_obj[-1].write(
							{'start_date':self.start_date,
							'end_date':self.end_date,
							'company_id':self.company_id.id,
							})
		if not invoice_obj:
			invoice_obj.create(
							{'start_date':self.start_date,
							'end_date':self.end_date,
							'company_id':self.company_id.id,
							})

		return self.env["report"].get_action(self, 'account.bi.mustroll.xlsx')



class CheckDate(models.Model):
	_name = 'check.date'

	start_date = fields.Date('From Date',default=fields.Datetime.now(), required=True)
	end_date = fields.Date('To Date',default=fields.Datetime.now(),required=True)
	company_id = fields.Many2one('res.company', string='Company', required=True)

