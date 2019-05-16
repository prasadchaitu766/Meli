from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models,_

class SaleIncentive(models.Model):
	_name = 'sale.incentive'
	_rec_name = 'employee_id'

	@api.depends('sale_incentive_line.amount')
	def _compute_amount(self):
		for order in self:
			amount_total = 0.0
			for line in order.sale_incentive_line:
				amount_total += line.amount
			order.update({
				'amount_total': amount_total,
			})
			
	name = fields.Char(string='Sequence',copy=False, readonly=True, index=True, default=lambda self: _('New'))
	employee_id = fields.Many2one('hr.employee', string="Employee",  required=True)
	sale_incentive_line = fields.One2many('sale.incentive.line', 'line_id', "Incentive")
	amount_total = fields.Monetary(compute='_compute_amount', string="Total", readonly=True, store=True)
	currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)

	@api.model
	def create(self, vals):
		if vals.get('name', _('New')) == _('New'):
			vals['name'] = self.env['ir.sequence'].next_by_code('sale.incentive') or _('New')			
		result = super(SaleIncentive, self).create(vals)	
		return result

class SaleIncentiveLine(models.Model):
	_name = 'sale.incentive.line'

	line_id = fields.Many2one('sale.incentive', "Incentive Line")
	date = fields.Date("Date")
	employee_id = fields.Many2one('hr.employee', string="Employee", related='line_id.employee_id', store=True)
	amount = fields.Float("Amount")
