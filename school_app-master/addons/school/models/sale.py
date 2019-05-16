# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError



class SaleOrder(models.Model):
	_inherit = "sale.order"
	

	school_id = fields.Many2one('school.school', 'Campus', required=False)
	partner_id = fields.Many2one('res.partner', string='Employee', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, required=True, change_default=True, index=True, track_visibility='always')


	@api.onchange('school_id')
	def onchange_school_id(self):
		for order in self:
			school_id = order.school_id
			if school_id:
				location_obj = self.env['stock.location']
				location = location_obj.search([('school_id','=',school_id.id)])
				warehouse_id=self.env['stock.warehouse'].search([('lot_stock_id','=',location.id)],limit=1)
				order.warehouse_id = warehouse_id.id

	@api.multi
	def action_confirm(self):
		result = super(SaleOrder, self).action_confirm()
		for order in self:
			order.picking_ids.write({'school_id': order.school_id.id})
		return result

	
	@api.multi
	def _prepare_invoice(self):
		"""
		Prepare the dict of values to create the new invoice for a sales order. This method may be
		overridden to implement custom invoice generation (making sure to call super() to establish
		a clean extension chain).
		"""
		self.ensure_one()
		journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
		if not journal_id:
			raise UserError(_('Please define an accounting sale journal for this company.'))
		invoice_vals = {
			'name': self.client_order_ref or '',
			'origin': self.name,
			'school_id': self.school_id.id,
			'type': 'out_invoice',
			'account_id': self.partner_invoice_id.property_account_receivable_id.id,
			'partner_id': self.partner_invoice_id.id,
			'partner_shipping_id': self.partner_shipping_id.id,
			'journal_id': journal_id,
			'currency_id': self.pricelist_id.currency_id.id,
			'comment': self.note,
			'payment_term_id': self.payment_term_id.id,
			'fiscal_position_id': self.fiscal_position_id.id or self.partner_invoice_id.property_account_position_id.id,
			'company_id': self.company_id.id,
			'user_id': self.user_id and self.user_id.id,
			'team_id': self.team_id.id
		}
		return invoice_vals

# class SaleOrderLine(models.Model):
#     _inherit = "sale.order.line"


#     school_id = fields.Many2one('school.school', 'Campus', related='order_id.school_id', store=True)
