# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError


class PurchaseOrder(models.Model):
	_inherit = "purchase.order"
	
	school_id = fields.Many2one('school.school', 'Campus', required=False)

	# @api.onchange('school_id')
	# def onchange_school_id(self):
	# 	for order in self:
	# 		school_id = order.school_id
	# 		if school_id:
	# 			location_obj = self.env['stock.location']
	# 			location = location_obj.search([('school_id','=',school_id.id)])
	# 			picking_obj = self.env['stock.picking.type']
	# 			picking = picking_obj.search([('code','=','incoming'),('default_location_dest_id','=',location.id)])
	# 			order.picking_type_id = picking.id

	@api.onchange('school_id')
	def onchange_branch(self):
		for order in self:
			school_id = order.school_id
			if school_id:
				location_obj = self.env['stock.location']
				location_count = location_obj.search([('school_id','=',school_id.id)],count=True)
				if location_count == 1:
					location = location_obj.search([('school_id','=',school_id.id)])
					picking_obj = self.env['stock.picking.type']
					picking = picking_obj.search([('code','=','incoming'),('default_location_dest_id','=',location.id)])
					order.picking_type_id = picking.id
				else:
					order.picking_type_id = ''


	@api.model
	def _prepare_picking(self):
		super(PurchaseOrder, self)._prepare_picking()
		return{
			'picking_type_id': self.picking_type_id.id,
			'partner_id': self.partner_id.id,
			'date': self.date_order,
			'origin': self.name,
			'location_dest_id': self._get_destination_location(),
			'location_id': self.partner_id.property_stock_supplier.id,
			'company_id': self.company_id.id,
			'school_id':self.school_id.id
		}

class PurchaseOrderLine(models.Model):
	_inherit = "purchase.order.line"

	school_id = fields.Many2one('school.school', 'Campus', related='order_id.school_id', store=True)

# need to check
# class AccountInvoice(models.Model):
# 	_inherit = "account.invoice"

# 	def _prepare_invoice_line_from_po_line(self, line):
# 		data = super(AccountInvoice,
# 					 self)._prepare_invoice_line_from_po_line(line)

# 		data['school_id'] = line.order_id.school_id.id
# 		return data


	



	