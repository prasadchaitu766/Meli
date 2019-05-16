# -*- coding: utf-8 -*-
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import xlsxwriter
import datetime
from datetime import datetime, date
import odoo.addons.decimal_precision as dp
import re
import string
from odoo.exceptions import UserError, ValidationError

class BiPayslipXlsx(ReportXlsx):
	def generate_xlsx_report(self, workbook, data, invoices):
		invoice_obj = self.env['bi.payslip.rep'].search([])[-1]		
		register_ids = self.env.context.get('active_ids', [])
		register_id = self.env['hr.payslip.run'].search([])
		
		net = 0.0
		for register in invoice_obj.batch_ids:
			# if register.id not in register_ids:
			# 	continue
			# date_from =invoice_obj.start_date
			# date_to =  invoice_obj.end_date
			# employee_id = invoice_obj.employee_id
			# result = {}
			# self.env.cr.execute("""
			# 	SELECT pl.id from hr_payslip_line as pl
			# 	LEFT JOIN hr_payslip AS hp on (pl.slip_id = hp.id)
			# 	WHERE (hp.date_from >= %s) AND (hp.date_to <= %s)
			# 	AND pl.register_id = %s
			# 	AND hp.state = 'draft' """ + (employee_id and " and hp.employee_id = " +str(employee_id) or "")+""" 
			# 	ORDER BY pl.slip_id, pl.sequence""",
			# 	(date_from, date_to, register.id))
			# line_ids = [x[0] for x in self.env.cr.fetchall()]
			worksheet = workbook.add_worksheet(str(register.company_id.name))

			var = self.env['hr.payroll.structure'].search([])
			
			new_row = 1
			# inc = 0
			row = 1
			col = 0
			
			y = 'Yes'
			n = 'No'
			
			for structure in var:
				inc = 8
				worksheet.set_column('A:K',15)
				alpha = list(string.ascii_uppercase)
				format = workbook.add_format({'bold': True, 'bg_color': 'cece79'})
				for alp in range(0,26):
					alpha.append('A'+str(alpha[alp]))
				
				worksheet.write('A%s' %(row), 'Employee Name')
				worksheet.write('B%s' %(row), 'Worked Days')
				worksheet.write('C%s' %(row), 'Company Name')
				worksheet.write('D%s' %(row), 'Designation')
				# worksheet.write('E%s' %(row), 'Net')
				worksheet.write('E%s' %(row), 'Offered Basic',format)
				worksheet.write('F%s' %(row), 'Offered DA',format)
				worksheet.write('G%s' %(row), 'Offered HRA',format)
				worksheet.write('H%s' %(row), 'Offered SA',format)
				worksheet.write('I%s' %(row), 'Offered Total Salary',format)
				
				employee_id = False
				# raise UserError((str(alpha)))
				format = workbook.add_format({'bold': True, 'bg_color': 'f9f965'})
				for res in self.env['hr.payslip'].search([('company_id','=',register.company_id.id),('payslip_run_id','=',register.id),('struct_id','=',structure.id)]): 
					for heading in self.env['hr.payslip.line'].search([('slip_id','=',res.id)]): 
						# raise UserError((str(heading)))
						if employee_id != heading.slip_id.employee_id.id:
							if employee_id:
								break
							employee_id = heading.slip_id.employee_id.id
						inc = inc + 1
						worksheet.write(alpha[inc]+'%s' %(row), heading.name,format)	
				inc = inc + 1
				worksheet.write(alpha[inc]+'%s' %(row), 'Net')		
				net_count = inc
				employee_id = False
				ls = []
				net = 0.0
				
				
				for rec in self.env['hr.payslip'].search([('company_id','=',register.company_id.id),('payslip_run_id','=',register.id),('struct_id','=',structure.id)]): 
					for line in self.env['hr.payslip.line'].search([('slip_id','=',rec.id)]): 
						if employee_id != line.slip_id.employee_id.id:
							employee_id = line.slip_id.employee_id.id
							if net > 0.0:
								worksheet.write(alpha[net_count]+'%s' %(new_row), net)
							new_row+=1
							inc = 9					
							net = float(rec.amount_total)
							worksheet.write('A%s' %(new_row), line.employee_id.name)
							worksheet.write('C%s' %(new_row), line.employee_id.company_id.name)
							worksheet.write('D%s' %(new_row), line.employee_id.job_id.name)
							# worksheet.write('E%s' %(new_row), rec.amount_total)
							worksheet.write('E%s' %(new_row), rec.contract_id.wage)
							worksheet.write('F%s' %(new_row), rec.contract_id.dearness_allowance)
							worksheet.write('G%s' %(new_row), rec.contract_id.house_rent_allowance)
							worksheet.write('H%s' %(new_row), rec.contract_id.special_allowance)
							worksheet.write('I%s' %(new_row), rec.contract_id.offered_salary)
							for worked in rec.worked_days_line_ids:
								if worked.code =='WORK100':
								   worksheet.write('B%s' %(new_row), worked.number_of_days)
								   break
						
						worksheet.write(alpha[inc]+'%s' %(new_row), line.amount)				
						inc = inc + 1
				if net > 0.0:
					worksheet.write(alpha[net_count]+'%s' %(new_row), net)
				row =new_row + 2
				new_row = new_row + 2


BiPayslipXlsx('report.account.bi.payslip.new.xlsx','hr.payslip.run')




