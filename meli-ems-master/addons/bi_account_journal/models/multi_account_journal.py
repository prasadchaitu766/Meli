from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp

#==================================================
# Class : BiMultiAccountReceipt
# Description : Multi Account Receipt Details
#==================================================
class BiMultiAccountReceipt(models.Model):
	_name = "bi.multi.account.receipt"
	_description = "Multi Account Receipt Details"
	
	@api.depends('receipt_ids.price_total')
	def _compute_total(self):
		for receipt in self:
			amount_untaxed = amount_tax = 0.0
			for line in receipt.receipt_ids:
				amount_untaxed += line.price_subtotal
				# FORWARDPORT UP TO 10.0
				if receipt.company_id.tax_calculation_rounding_method == 'round_globally':
					taxes = line.tax_id.compute_all(line.amount, line.currency_id, 1, product=False, partner=False)
					amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
				else:
					amount_tax += line.price_tax
			receipt.update({
				'subtotal': receipt.currency_id.round(amount_untaxed),
				'amount_tax': receipt.currency_id.round(amount_tax),
				'total': amount_untaxed + amount_tax,
			})
	
	name = fields.Char(string="Sequence No", required=True, Index= True, default=lambda self:('New'), readonly=True, states={'draft': [('readonly',False)]})
	receipt_date = fields.Date(string="Receipt Date", default=fields.Date.context_today, required=True, readonly=True, states={'draft': [('readonly',False)]})
	journal_id =  fields.Many2one('account.journal',string="Journal ID", required=True, readonly=True, states={'draft': [('readonly',False)]}, domain=[('type', 'in', ('bank', 'cash'))])  
	account_id = fields.Many2one('account.account',string="Account ID" , required=True, readonly=True, states={'draft': [('readonly',False)]})
	receipt_ids =  fields.One2many('bi.multi.account.receipt.line','receipt_id',string="Accounts",readonly=True, states={'draft': [('readonly', False)]})
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id,readonly=True, states={'draft': [('readonly', False)]})
	move_id = fields.Many2one('account.move', string='Journal Entry',readonly=True, index=True, ondelete='restrict', copy=False,
		help = "Link to the automatically generated Journal Items.")
	state = fields.Selection([
		('draft', 'Draft'),
		('post', 'Posted'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'), states={'post': [('readonly',True)]})
	total = fields.Monetary(compute='_compute_total', string='Total', readonly=True, store=True)
	amount_tax = fields.Monetary(string='Amount Tax',store=True, readonly=True, compute='_compute_total',digits_compute=dp.get_precision('Product Price'))
	subtotal = fields.Monetary(string='Sub Total',store=True, readonly=True, compute='_compute_total',digits_compute=dp.get_precision('Product Price'))
	bank_type = fields.Selection([('cheque','Cheque'),('ntfs','NTFS'),('cash','Cash'),('others','Others')],string="Payment Type",readonly=True, states={'draft': [('readonly', False)]})
	cheque_no = fields.Char("Cheque Number")
	Cheque_date = fields.Date("Cheque Date")
	
	
	@api.onchange('journal_id')
	def onchange_journal_id(self):
		if self.journal_id:
			self.account_id = self.journal_id.default_debit_account_id

	
	
	# @api.model
	# def create(self, vals):
	# 	if vals.get('name', _('New')) == _('New'):
	# 		if 'company_id' in vals:
	# 			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('bi.multi.account.receipt') or _('New')
	# 		else:
	# 			vals['name'] = self.env['ir.sequence'].next_by_code('bi.multi.account.receipt') or _('New')

				
	# 	result = super(BiMultiAccountReceipt, self).create(vals)
	# 	return result

	
	@api.multi
	def button_post(self):
		aml_dict = {}
		total=0.0
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		for receipt in self:
			dst_move = self.env['account.move'].create({
														# 'name': receipt.name,
														'date': receipt.receipt_date,
														'ref':'Receipt',
														'company_id': receipt.company_id.id,
														'journal_id':receipt.journal_id.id,
														})
			for line in receipt.receipt_ids:
				i=1
				aml_dict={
						'name':(receipt.cheque_no and '-'+str(receipt.cheque_no) or '')+'-'+(line.name and str(line.name) or ''),
						'account_id': line.account_id.id,
						'currency_id': receipt.currency_id.id,	            
						'journal_id': receipt.journal_id.id,
						'debit':0.0,
						'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
						'credit':line.amount,
						'partner_id':line.customer.id,
						'move_id':dst_move.id,
					}
				total = total + line.price_subtotal
				aml_obj.create(aml_dict)
				if line.tax_id:
					for tax in line.tax_id.compute_all(line.amount, line.currency_id, 1)['taxes']:
						aml_dict={
						'name':_('Tax') + ' ' + tax['name'],
						'account_id': tax['account_id'],
						'debit': ((tax['amount'] < 0) and -tax['amount']) or 0.0,
						'credit': ((tax['amount'] > 0) and tax['amount']) or 0.0,
						'move_id':dst_move.id,
						'analytic_account_id': tax['analytic'] and line.analytic_account_id.id or False,
						}
						aml_obj.create(aml_dict)
						total = total +tax['amount']
			if total> 0:
				aml_dict.update({
					'name': (receipt.cheque_no and '-'+str(receipt.cheque_no) or '')+'-'+(line.name and str(line.name) or ''),
					'account_id': receipt.journal_id.default_debit_account_id.id,
					'currency_id': receipt.currency_id.id,	            
					'journal_id': receipt.journal_id.id,
					'credit':0.0,
					'debit':total,
					'analytic_account_id':False,
					'partner_id':False,
					# line.customer.id,
					'move_id':dst_move.id})            
				aml_obj.create(aml_dict)
			dst_move.post()
			receipt.write({'state':'post','move_id':dst_move.id,'name':dst_move.name})

	@api.multi
	def button_cancel(self):
		self.move_id.button_cancel()
		move_id = self.move_id
		self.write({'state': 'cancel','move_id' : False})
		move_id.unlink()

	@api.multi
	def button_draft(self):		
		self.write({'state': 'draft'})

	@api.multi
	def unlink(self):
		for order in self:
			if order.state not in ('draft'):
				raise UserError(_('You can not delete receipt voucher'))
		return super(BiMultiAccountReceipt, self).unlink()

	


	

#==================================================
# Class : BiMultiAccountReceiptLine
# Description : Multi Account Receipt Line
#==================================================
class BiMultiAccountReceiptLine(models.Model):
	_name = "bi.multi.account.receipt.line"
	_description = "Multi Account Receipt Line"
	
	
	@api.depends('amount', 'tax_id')
	def _compute_amount(self):
		for line in self:
			taxes = line.tax_id.compute_all(line.amount, line.currency_id,1, product=False, partner=False)
			line.update({
				'price_tax': taxes['total_included'] - taxes['total_excluded'],
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})
	
	receipt_id = fields.Many2one('bi.multi.account.receipt',string="Receipt")
	analytic_account_id = fields.Many2one('account.analytic.account',"Analytic Account")
	account_id = fields.Many2one('account.account', domain=[] , string="Account ID", required=True)
	customer = fields.Many2one('res.partner', string = "Customer", required=True)
	name = fields.Char(string="Description", required=True)
	amount = fields.Float(string="Amount", required=True)
	tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
	currency_id = fields.Many2one('res.currency', related='receipt_id.currency_id', store=True, related_sudo=False,readonly=True, states={'draft': [('readonly', False)]})
	price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
	price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
	price_tax = fields.Monetary(compute='_compute_amount', string='Tax', store=True)

	
		
#==================================================
# Class : BiMultiAccountPayment
# Description : Multi Account Payment Details
#==================================================
class BiMultiAccountPayment(models.Model):
	_name = "bi.multi.account.payment"
	_description = "Multi Account Payment Details"
	
	@api.depends('payment_ids.price_total')
	def _compute_total(self):
		for payment in self:
			amount_untaxed = amount_tax = 0.0
			for line in payment.payment_ids:
				amount_untaxed += line.price_subtotal
				# FORWARDPORT UP TO 10.0
				if payment.company_id.tax_calculation_rounding_method == 'round_globally':
					taxes = line.tax_id.compute_all(line.amount, line.currency_id, 1, product=False, partner=False)
					amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
				else:
					amount_tax += line.price_tax
			payment.update({
				'subtotal': payment.currency_id.round(amount_untaxed),
				'amount_tax': payment.currency_id.round(amount_tax),
				'total': amount_untaxed + amount_tax,
			})
			
	name = fields.Char(string="Sequence No", required=True, Index= True, default=lambda self:('New'), readonly=True, states={'draft': [('readonly',False)]})
	payment_date = fields.Date(string="Payment Date", default=fields.Date.context_today, required=True, readonly=True, states={'draft': [('readonly',False)]})
	journal_id =  fields.Many2one('account.journal',string="Journal ID", required=True, readonly=True, states={'draft': [('readonly',False)]}, domain=[('type', 'in', ('bank', 'cash'))])  
	account_id =  fields.Many2one('account.account', string="Account ID", required=True, readonly=True, states={'draft': [('readonly',False)]})
	payment_ids =  fields.One2many('bi.multi.account.payment.line','receipt_id',string="Accounts",readonly=True, states={'draft': [('readonly', False)]})
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id)
	move_id = fields.Many2one('account.move', string='Journal Entry',readonly=True, index=True, ondelete='restrict', copy=False,
		help = "Link to the automatically generated Journal Items.")	
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'), states={'post': [('readonly',True)]})
	state = fields.Selection([
		('draft', 'Draft'),
		('post', 'Posted'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	total = fields.Monetary(compute='_compute_total', string='Total', readonly=True, store=True)
	amount_tax = fields.Monetary(string='Amount Tax',store=True, readonly=True, compute='_compute_total',digits_compute=dp.get_precision('Product Price'))
	subtotal = fields.Monetary(string='Sub Total',store=True, readonly=True, compute='_compute_total',digits_compute=dp.get_precision('Product Price'))
	bank_type = fields.Selection([('cheque','Cheque'),('ntfs','NTFS'),('cash','Cash'),('others','Others')],string="Payment Type", states={'draft': [('readonly', False)]})
	cheque_no = fields.Char("Cheque Number")
	Cheque_date = fields.Date("Cheque Date")	
	
	
	# @api.onchange('journal_id')
	# def _onchange_journal_id(self):
	# 	if self.journal_id:
	# 		self.account_id = self.journal_id.account_id

	@api.onchange('journal_id')
	def onchange_journal_id(self):
		if self.journal_id:
			self.account_id = self.journal_id.default_credit_account_id
		
	@api.multi
	def button_cancel(self):
		self.move_id.button_cancel()
		move_id = self.move_id
		self.write({'state': 'cancel','move_id' : False})
		move_id.unlink()

	@api.multi
	def button_draft(self):		
		self.write({'state': 'draft'})

	# @api.model
	# def create(self, vals):
	# 	if vals.get('name', _('New')) == _('New'):
	# 		if 'company_id' in vals:
	# 			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('bi.multi.account.payment') or _('New')
	# 		else:
	# 			vals['name'] = self.env['ir.sequence'].next_by_code('bi.multi.account.payment') or _('New')

				
	# 	result = super(BiMultiAccountPayment, self).create(vals)
	# 	return result

	@api.multi
	def button_post(self):
		aml_dict = {}
		total=0.0
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		for payment in self:
			dst_move = self.env['account.move'].create({
														# 'name': payment.name,
														'date': payment.payment_date,
														'ref':'Payment',
														'company_id': payment.company_id.id,
														'journal_id':payment.journal_id.id,
														})
			for line in payment.payment_ids:
				i=1
				aml_dict={
						'name':(payment.cheque_no and '-'+str(payment.cheque_no) or '')+'-'+(line.name and str(line.name) or ''),
						'account_id': line.account_id.id,
						'currency_id': payment.currency_id.id,	            
						'journal_id': payment.journal_id.id,
						'debit':line.amount,
						'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
						'credit':0.0,
						'partner_id':line.customer.id,
						'move_id':dst_move.id,
					}
				total = total + line.price_subtotal
				aml_obj.create(aml_dict)
				if line.tax_id:
					for tax in line.tax_id.compute_all(line.amount, line.currency_id, 1)['taxes']:
						aml_dict={
						'name':_('Tax') + ' ' + tax['name'],
						'account_id': tax['account_id'],
						'debit': ((tax['amount'] > 0) and tax['amount']) or 0.0,
						'credit': ((tax['amount'] < 0) and -tax['amount']) or 0.0,
						'move_id':dst_move.id,
						'analytic_account_id': tax['analytic'] and line.analytic_account_id.id or False,
						}
						aml_obj.create(aml_dict)
						total = total +tax['amount']
			if total> 0:
				aml_dict.update({
					'name':(payment.cheque_no and '-'+str(payment.cheque_no) or '')+'-'+(line.name and str(line.name) or ''),
					'account_id': payment.journal_id.default_debit_account_id.id,
					'currency_id': payment.currency_id.id,	            
					'journal_id': payment.journal_id.id,
					'credit':total,
					'debit':0.0,
					'analytic_account_id':False,
					'partner_id':False,#line.customer.id,
					'move_id':dst_move.id})            
				aml_obj.create(aml_dict)
			dst_move.post()
			payment.write({'state':'post','move_id':dst_move.id,'name':dst_move.name})


	@api.multi
	def unlink(self):
		for order in self:
			if order.state not in ('draft'):
				raise UserError(_('You can not delete payment voucher'))
		return super(BiMultiAccountPayment, self).unlink()

	

	
#==================================================
# Class : BiMultiAccountPaymentLine
# Description : Multi Account Payment Line
#==================================================
class BiMultiAccountPaymentLine(models.Model):
	_name = "bi.multi.account.payment.line"
	_description = "Multi Account Payment Line"
	
	@api.depends('amount', 'tax_id')
	def _compute_amount(self):
		for line in self:
			taxes = line.tax_id.compute_all(line.amount, line.currency_id,1, product=False, partner=False)
			line.update({
				'price_tax': taxes['total_included'] - taxes['total_excluded'],
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})
			
	receipt_id = fields.Many2one('bi.multi.account.payment', string="Receipt")
	account_id = fields.Many2one('account.account', domain=[], string="Account ID", required=True)
	analytic_account_id = fields.Many2one('account.analytic.account',"Analytic Account")
	customer = fields.Many2one('res.partner', string = "Customer", required=True)
	name = fields.Char(string="Description", required=True)
	amount = fields.Float(string="Amount", required=True)
	currency_id = fields.Many2one('res.currency', related='receipt_id.currency_id', store=True, related_sudo=False)
	price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
	price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
	price_tax = fields.Monetary(compute='_compute_amount', string='Tax', store=True)
	tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])


