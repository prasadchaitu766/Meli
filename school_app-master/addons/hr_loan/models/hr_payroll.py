from odoo import api, fields, models, tools, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from openerp.osv import osv
from odoo.exceptions import UserError, AccessError


class HrPayslip(models.Model):
	_inherit = 'hr.payslip'
	
	@api.one
	def compute_total_paid_loan(self):
		total = 0.00
		for line in self.loan_ids:
			if line.paid == True:
				total += line.paid_amount
		self.total_amount_paid = total
	
	total_amount_paid = fields.Float(string="Total Loan Amount", compute= 'compute_total_paid_loan')
	
	
	@api.multi
	def compute_sheet(self):
		for payslip in self:
			loan_amount = 0.0
			loan = self.env['hr.loan.line'].search([('employee_id','=',payslip.employee_id.id),('paid_date','>=',payslip.date_from),('paid_date','<=',payslip.date_to),('paid','=',False),('loan_id.state','=','approve')])
			for res in loan:
				payslip_input= self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=','LO')])
				if payslip_input:
					loan_amount += res.paid_amount
				payslip_input.write({
					'amount':loan_amount
					})
					
		result = super(HrPayslip, self).compute_sheet()           
		return True		
	
	@api.multi
	def action_payslip_done(self):
		result = super(HrPayslip, self).action_payslip_done()
		array = []
		loan = self.env['hr.loan.line'].search([('employee_id','=',self.employee_id.id),('paid_date','>=',self.date_from),('paid_date','<=',self.date_to),('paid','=',False),('loan_id.state','=','approve')])
		for res in loan:
			array.append(res.id)
			res.action_paid_amount()
		return result