# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError


class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	@api.model
	def _default_picking_transfer(self):
		type_obj = self.env['stock.picking.type']
		company_id = self.env.context.get('company_id') or self.env.user.company_id.id
		types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id)], limit=1)
		if not types:
			types = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id', '=', False)])
		return types.id

	school_id = fields.Many2one('school.school', 'Campus', required=False)
	picking_count = fields.Integer(string="Count")
	invoice_picking_id = fields.Many2one('stock.picking', string="Picking Id")
	picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=True,
									  default=_default_picking_transfer,
									  help="This will determine picking type of incoming shipment")


	# @api.onchange('partner_id', 'company_id')
	# def _onchange_partner_id(self):
	# 	res = super(AccountInvoice, self)._onchange_partner_id()
	# 	if not self.env.context.get('default_journal_id') and self.partner_id and self.currency_id and\
	# 			self.type in ['in_invoice', 'in_refund'] and\
	# 			self.currency_id != self.partner_id.property_purchase_currency_id:
	# 		journal_domain = [
	# 			('type', '=', 'purchase'),
	# 			('company_id', '=', self.company_id.id),
	# 			('currency_id', '=', self.partner_id.property_purchase_currency_id.id),
	# 		]
	# 		default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
	# 		if default_journal_id:
	# 			self.journal_id = default_journal_id
	# 		self.school_id = self.partner_id.school_id
			
	# 	return res
	
	@api.multi
	def action_move_create(self):
		""" Creates invoice related analytics and financial move lines """
		account_move = self.env['account.move']

		for inv in self:
			if not inv.journal_id.sequence_id:
				raise UserError(_('Please define sequence on the journal related to this invoice.'))
			if not inv.invoice_line_ids:
				raise UserError(_('Please create some invoice lines.'))
			if inv.move_id:
				continue

			ctx = dict(self._context, lang=inv.partner_id.lang)

			if not inv.date_invoice:
				inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
			company_currency = inv.company_id.currency_id

			# create move lines (one per invoice line + eventual taxes and analytic lines)
			iml = inv.invoice_line_move_line_get()
			iml += inv.tax_line_move_line_get()

			diff_currency = inv.currency_id != company_currency
			# create one move line for the total and possibly adjust the other lines amount
			total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, iml)

			name = inv.name or '/'
			if inv.payment_term_id:
				totlines = inv.with_context(ctx).payment_term_id.with_context(currency_id=company_currency.id).compute(total, inv.date_invoice)[0]
				res_amount_currency = total_currency
				ctx['date'] = inv._get_currency_rate_date()
				for i, t in enumerate(totlines):
					if inv.currency_id != company_currency:
						amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
					else:
						amount_currency = False

					# last line: add the diff
					res_amount_currency -= amount_currency or 0
					if i + 1 == len(totlines):
						amount_currency += res_amount_currency

					iml.append({
						'type': 'dest',
						'name': name,
						'price': t[1],
						'account_id': inv.account_id.id,
						'date_maturity': t[0],
						'amount_currency': diff_currency and amount_currency,
						'currency_id': diff_currency and inv.currency_id.id,
						'invoice_id': inv.id
					})
			else:
				iml.append({
					'type': 'dest',
					'name': name,
					'price': total,
					'account_id': inv.account_id.id,
					'date_maturity': inv.date_due,
					'amount_currency': diff_currency and total_currency,
					'currency_id': diff_currency and inv.currency_id.id,
					'invoice_id': inv.id
				})
			part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
			line = [(0, 0, self.line_get_convert(l, part.id)) for l in iml]
			line = inv.group_lines(iml, line)

			journal = inv.journal_id.with_context(ctx)
			line = inv.finalize_invoice_move_lines(line)

			date = inv.date or inv.date_invoice
			move_vals = {
				'ref': inv.reference,
				'line_ids': line,
				'journal_id': journal.id,
				'date': date,
				'narration': inv.comment,
				'school_id': inv.school_id.id,
			}
			ctx['company_id'] = inv.company_id.id
			ctx['invoice'] = inv
			ctx_nolang = ctx.copy()
			ctx_nolang.pop('lang', None)
			move = account_move.with_context(ctx_nolang).create(move_vals)
			# Pass invoice in context in method post: used if you want to get the same
			# account move reference when creating the same invoice after a cancelled one:
			move.post()
			# make the invoice point to that move
			vals = {
				'move_id': move.id,
				'date': date,
				'move_name': move.name,
			}
			inv.with_context(ctx).write(vals)
		return True

	@api.multi
	def action_invoice_open(self):
		invoice = super(AccountInvoice,self).action_invoice_open()
		type_obj = self.env['stock.picking.type']
		company_id = self.env.context.get('company_id') or self.env.user.company_id.id
		picking_type_id = type_obj.search([('code', '=', 'outgoing'), ('warehouse_id.company_id', '=', company_id),('warehouse_id.school_id','=',self.school_id.id)], limit=1)
		for invoice in self:
			if invoice.student_payslip_id:
				for order_line in invoice.invoice_line_ids:
					if order_line.product_id and order_line.product_id.type == "product":							
						if not self.invoice_picking_id:
							pick = {
								'school_id': self.school_id.id,
								'picking_type_id': picking_type_id.id,
								'partner_id': self.partner_id.id,
								'origin': self.number,
								'location_dest_id': self.partner_id.property_stock_customer.id,
								'location_id': picking_type_id.default_location_src_id.id
							}
							picking = self.env['stock.picking'].create(pick)
							self.invoice_picking_id = picking.id
							self.picking_count = len(picking)
							moves = invoice.invoice_line_ids.filtered(lambda r: r.product_id.type in ['product', 'consu'])._create_stock_moves(picking)
							move_ids = moves.action_confirm()
							move_ids.action_assign()
							move_ids.action_done()
		return invoice

	@api.multi
	def action_view_picking(self):
		action = self.env.ref('stock.action_picking_tree_ready')
		result = action.read()[0]
		result.pop('id', None)
		result['context'] = {}
		result['domain'] = [('id', '=', self.invoice_picking_id.id)]
		pick_ids = sum([self.invoice_picking_id.id])
		if pick_ids:
			res = self.env.ref('stock.view_picking_form', False)
			result['views'] = [(res and res.id or False, 'form')]
			result['res_id'] = pick_ids or False
		return result
		
	@api.onchange('purchase_id')
	def purchase_order_change(self):
		# res = 
		if self.purchase_id:
			self.school_id = self.purchase_id.school_id.id

		return super(AccountInvoice,self).purchase_order_change()

class SupplierInvoiceLine(models.Model):
	_inherit = 'account.invoice.line'
	
	school_id = fields.Many2one('school.school', 'Campus', related='invoice_id.school_id', store=True)

	@api.multi
	def _create_stock_moves(self, picking):
		moves = self.env['stock.move']
		done = self.env['stock.move'].browse()
		for line in self:
			price_unit = line.price_unit
			template = {
				'name': line.name or '',
				'product_id': line.product_id.id,
				'product_uom': line.uom_id.id,
				'location_id': picking.picking_type_id.default_location_src_id.id,
				'location_dest_id': line.invoice_id.partner_id.property_stock_customer.id,
				'picking_id': picking.id,
				'move_dest_id': False,
				'state': 'draft',
				'company_id': line.invoice_id.company_id.id,
				'price_unit': price_unit,
				'picking_type_id': picking.picking_type_id.id,
				'procurement_id': False,
				'route_ids': 1 and [
					(6, 0, [x.id for x in self.env['stock.location.route'].search([('id', 'in', (2, 3))])])] or [],
				'warehouse_id': picking.picking_type_id.warehouse_id.id,
			}
			diff_quantity = line.quantity
			tmp = template.copy()
			tmp.update({
				'product_uom_qty': diff_quantity,
			})
			template['product_uom_qty'] = diff_quantity
			done += moves.create(template)
		return done



class AccountMove(models.Model):
	_inherit = "account.move"
	
	school_id = fields.Many2one('school.school', 'Campus', required=False)


# class AccountInvoiceLine(models.Model):
# 	_inherit = "account.invoice.line"

# 	school_id = fields.Many2one('school.school', 'Campus', related='invoice_id.school_id', store=True)


# class HrExpense(models.Model):

# 	_inherit = "hr.expense"
	
	
	

	
