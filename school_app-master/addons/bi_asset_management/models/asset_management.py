from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero

class AccountInvoice(models.Model):
	_inherit = 'account.invoice'
 
	asset_mids = fields.One2many('account.asset.asset','invoice_id')

	@api.multi
	def action_move_create(self):
		result = super(AccountInvoice, self).action_move_create()
		# asset = self.env['account.asset.asset']
		# inv.invoice_line_ids.unlink()

		for inv in self:
			context = dict(self.env.context)
			# Within the context of an invoice,
			# this default value is for the type of the invoice, not the type of the asset.
			# This has to be cleaned from the context before creating the asset,
			# otherwise it tries to create the asset with the type of the invoice.
			context.pop('default_type', None)
			inv.asset_mids.unlink()

			inv.invoice_line_ids.with_context(context).create_asset()
		return result

class AccountInvoiceLine(models.Model):
	_inherit = 'account.invoice.line'

	split = fields.Boolean(string="Split", copy=False)	

	@api.one
	def create_asset(self):		
		for inv in self:
			if inv.product_id.asset == True:
				if inv.asset_category_id:
					if inv.split == True:
						quant = range(int(inv.quantity))
						for val in quant:
							vals = {
							'name': inv.name,
							'code': inv.invoice_id.number or False,
							'custodian': inv.env.user.id,
							'category_id': inv.asset_category_id.id,
							'value': inv.price_subtotal_signed/inv.quantity,
							'partner_id': inv.invoice_id.partner_id.id,
							'company_id': inv.invoice_id.company_id.id,
							'currency_id': inv.invoice_id.company_currency_id.id,
							'date': inv.invoice_id.date_invoice,
							'invoice_id': inv.invoice_id.id,
							'product_id':inv.product_id.id,
							'school_id': inv.invoice_id.school_id.id,
							}
							# changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
							# vals.update(changed_vals['value'])
							asset = self.env['account.asset.asset'].create(vals)
					elif inv.split == False:
						vals = {
							'name': inv.name,
							'code': inv.invoice_id.number or False,
							'custodian': inv.env.user.id,
							'category_id': inv.asset_category_id.id,
							'value': inv.price_subtotal_signed,
							'partner_id': inv.invoice_id.partner_id.id,
							'company_id': inv.invoice_id.company_id.id,
							'currency_id': inv.invoice_id.company_currency_id.id,
							'date': inv.invoice_id.date_invoice,
							'invoice_id': inv.invoice_id.id,
							'product_id':inv.product_id.id,
							'school_id': inv.invoice_id.school_id.id,
							}
						# changed_vals = self.env['account.asset.asset'].onchange_category_id_values(vals['category_id'])
						# vals.update(changed_vals['value'])
						asset = self.env['account.asset.asset'].create(vals)	

					if inv.asset_category_id.open_asset:
						asset.validate()
				return True
		
class AccountAssetAsset(models.Model):
	_inherit = 'account.asset.asset'

	seq = fields.Char(string="Sequence No", required=True, Index= True, default=lambda self:('New'), readonly=True)
	employee_id = fields.Many2one('hr.employee',string="Employee")
	custodian = fields.Many2one('res.users',string="Custodian")
	serial_no = fields.Char(string="Serial No", required=False)
	product_id = fields.Many2one('product.product')
	school_id = fields.Many2one('school.school',string="Campus")
	active = fields.Boolean(default=True)


	@api.onchange('employee_id')
	def onchange_product_id(self):
		for vals in self:
			if vals.employee_id:
				vals.custodian = vals.employee_id.user_id
				vals.school_id = vals.employee_id.school_id
			

	@api.model
	def create(self, vals):
		if vals.get('seq', _('New')) == _('New'):
			if 'company_id' in vals:
				vals['seq'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('account.asset.asset') or _('New')
			else:
				vals['seq'] = self.env['ir.sequence'].next_by_code('account.asset.asset') or _('New')
		# emp_id=vals['employee_id']
		# emp=self.env['hr.employee'].search([('id','=',emp_id)])
		# vals['custodian'] = emp.user_id
				
		result = super(AccountAssetAsset, self).create(vals)
		return result

	# @api.multi
	# def write(self, vals):	
	# 	emp_id = vals.get('employee_id')
	# 	emp = self.env['hr.employee'].search([('id','=',emp_id)])
	# 	value = emp.user_id.id
	# 	# raise UserError(str(value))
	# 	vals['custodian'] = value
	# 	assets = super(AccountAssetAsset, self).write(vals)
	# 	return assets

	@api.multi
	def name_get(self):
		result = []
		for record in self:
			name = '[' + str(record.name) + ']' + '- ' + str(record.serial_no)
			result.append((record.id, name))
		return result


class ProductTemplate(models.Model):
	_inherit = 'product.template'

	asset = fields.Boolean(string="Asset", copy=False)	
	list_price = fields.Float(default=0.0)



class AccountAssetDepreciationLine(models.Model):
	_inherit = 'account.asset.depreciation.line'


	school_id = fields.Many2one('school.school',string="Campus")
	@api.multi
	def create_move(self, post_move=True):
		created_moves = self.env['account.move']
		prec = self.env['decimal.precision'].precision_get('Account')
		for line in self:
			if line.move_id:
				raise UserError(_('This depreciation is already linked to a journal entry! Please post or delete it.'))
			category_id = line.asset_id.category_id
			depreciation_date = self.env.context.get('depreciation_date') or line.depreciation_date or fields.Date.context_today(self)
			company_currency = line.asset_id.company_id.currency_id
			current_currency = line.asset_id.currency_id
			# school_id = line.asset_id.school_id.id
			amount = current_currency.with_context(date=depreciation_date).compute(line.amount, company_currency)
			asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
			move_line_1 = {
				'name': asset_name,
				'account_id': category_id.account_depreciation_id.id,
				'debit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
				'credit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
				'journal_id': category_id.journal_id.id,
				'partner_id': line.asset_id.partner_id.id,
				'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'sale' else False,
				'currency_id': company_currency != current_currency and current_currency.id or False,
				'amount_currency': company_currency != current_currency and - 1.0 * line.amount or 0.0,
			}
			move_line_2 = {
				'name': asset_name,
				'account_id': category_id.account_depreciation_expense_id.id,
				'credit': 0.0 if float_compare(amount, 0.0, precision_digits=prec) > 0 else -amount,
				'debit': amount if float_compare(amount, 0.0, precision_digits=prec) > 0 else 0.0,
				'journal_id': category_id.journal_id.id,
				'partner_id': line.asset_id.partner_id.id,
				'analytic_account_id': category_id.account_analytic_id.id if category_id.type == 'purchase' else False,
				'currency_id': company_currency != current_currency and current_currency.id or False,
				'amount_currency': company_currency != current_currency and line.amount or 0.0,
			}
			move_vals = {
				'ref': line.asset_id.code,
				'school_id': line.asset_id.school_id.id,
				'date': depreciation_date or False,
				'journal_id': category_id.journal_id.id,
				'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
			}
			move = self.env['account.move'].create(move_vals)
			line.write({'move_id': move.id, 'move_check': True})
			created_moves |= move

		if post_move and created_moves:
			created_moves.filtered(lambda m: any(m.asset_depreciation_ids.mapped('asset_id.category_id.open_asset'))).post()
		return [x.id for x in created_moves]
