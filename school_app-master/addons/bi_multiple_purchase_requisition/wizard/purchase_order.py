from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
import math

class CreatePurchaseOrder(models.TransientModel):
	_name = 'create.purchase.order'
	_description = 'create purchase order from purchase requisition'

	partner_id = fields.Many2one('res.partner', string="Choose Vendor")
	item_ids = fields.Many2one('purchase.requisition',string='Items')

	@api.multi
	def create_purchase_order(self):
		lines = []
		requisition = self.env['purchase.requisition']
		vendors_list = self.env['res.partner'].search([('supplier','=',True)])
		# raise UserError(str(vendors_list))
		if self.partner_id:
			for items in requisition.browse(self._context.get('active_ids')):
				if items.state == "done":
					raise UserError(str("Can not create purchase quotation for done purchase requisition."))
				else:
					for item_line in items.line_ids:
						for vendor in item_line.product_id.seller_ids:
							if vendor.name == self.partner_id:
								line = {
									'product_id': item_line.product_id.id,
									'name': item_line.product_id.name,
									'price_unit':item_line.product_id.standard_price,
									'uom': item_line.product_uom_id.id,
									'product_qty': item_line.product_qty,
									'requisition_title': items.name
								}
								lines.append(line)

			if lines:
				view = self.env.ref('purchase.purchase_order_form')
				purchase = self.env['purchase.order'].create({
															'partner_id': self.partner_id.id,		
															'origin': "",})
				data = []
				for line in lines:
					self.env['purchase.order.line'].create({
							'product_id': line["product_id"],
							'name': line["name"],
							'product_uom': line["uom"],
							'date_planned': datetime.now(),
							'price_unit':line["price_unit"],
							'product_qty': line["product_qty"],
							'order_id': purchase.id,
						})
					data.append(line["requisition_title"])
				data = list(set(data))
				purchase.update({'origin':','.join(data)})
			
				return {
						'type': 'ir.actions.act_window',
						'name': 'Create RFQ',
						'type': 'ir.actions.act_window',
						'view_type': 'form',
						'view_mode': 'form',
						'res_model': 'purchase.order',
						'views': [(view.id, 'form')],
						'view_id': view.id,
						'target': 'new',
						'res_id': purchase.id,
						'context': self.env.context,
					}

		else:
			# for vendors in vendors_list:
			values = {}
			for items in requisition.browse(self._context.get('active_ids')):
				if items.state == "done":
					raise UserError(str("Can not create purchase quotation for done purchase requisition"))
				else:
					for item_line in items.line_ids:
						if not item_line.product_id.seller_ids:
							raise UserError(str("Vendor is not set for %s in purchase requisition %s")%(item_line.product_id.name,items.name))					
						for vendor in item_line.product_id.seller_ids:
							if values.get(vendor.name,False):
								values[vendor.name].append(item_line)
							else:
								values[vendor.name]=[item_line]
			for vendor in values:
				purchase = self.env['purchase.order'].create({
														'partner_id': vendor.id,
														'origin':""})
				source = []
				for line in values[vendor]:
					self.env['purchase.order.line'].create({
							'product_id': line.product_id.id,
							'name': line.product_id.name,
							'product_uom': line.product_uom_id.id,
							'date_planned': datetime.now(),
							'price_unit':line.price_unit,
							'product_qty': line.product_qty,
							'order_id': purchase.id,
						})
					source.append(line.requisition_id.name)
				source = list(set(source))
				purchase.update({'origin':','.join(source)})
