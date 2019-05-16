# -*- coding: utf-8 -*-
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import xlsxwriter
import datetime
from datetime import datetime, date
import odoo.addons.decimal_precision as dp
import re
import string
from odoo.exceptions import UserError, ValidationError

class BiWagesXlsx(ReportXlsx):
	def generate_xlsx_report(self, workbook, data, invoices):
		invoice_obj = self.env['bi.wages.rep'].search([])[-1]		
		register_ids = self.env.context.get('active_ids', [])
		register_id = self.env['hr.payslip.run'].search([])
		
		for register in invoice_obj.wage_ids:
			worksheet = workbook.add_worksheet(register.company_id.name)
			boldc = workbook.add_format({'bold': True,'align': 'center'})
			bold = workbook.add_format({'bold': True})
			right = workbook.add_format({'align': 'right'})
			merge_format = workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			})
			format_hidden = workbook.add_format({
			'hidden': True
			})

			row = 1
			col = 0
			new_row = row + 5
			y = 'Yes'
			n = 'No'

			worksheet.merge_range('A1:T1', 'FORM NO.XI' , merge_format)
			worksheet.merge_range('A2:T2', 'REGISTER OF WAGES' , merge_format)
			worksheet.merge_range('A3:T3', 'See Rule 29(1)' , merge_format)
			worksheet.merge_range('A4:T4', 'Name of Establishment    TP TLES AND SANITARIES ,PARAYANCHERRY, CALICUT  REG NO: 407/11-I/KII Vol.2'   , merge_format)
			worksheet.merge_range('A5:A6', 'Sl No' , merge_format)
			worksheet.merge_range('B5:B6', 'Name of Employee' , merge_format)
			worksheet.merge_range('C5:C6', 'Designation' , merge_format)
			worksheet.merge_range('D5:E5', 'Minimum wages payable' , merge_format)
			worksheet.merge_range('F5:G5', 'Rate of Wages Actually Paid' , merge_format)
			worksheet.write('D6%s', 'Basic', boldc)
			worksheet.write('E6%s', 'DA', boldc)
			worksheet.write('F6%s', 'Basic', boldc)
			worksheet.write('G6%s', 'DA', boldc)
			worksheet.merge_range('H5:H6', 'Total Attendance/ Days of work done' , merge_format)
			worksheet.merge_range('I5:I6', 'Overtime Worked' , merge_format)
			worksheet.merge_range('J5:J6', 'Other Allowance' , merge_format)
			worksheet.merge_range('K5:K6', 'Gross Salary Payable' , merge_format)
			worksheet.merge_range('L5:L6', 'Incentive' , merge_format)
			worksheet.merge_range('M5:Q5', 'DEDUCTIONS' , merge_format)
			worksheet.write('M6%s', 'EPF', boldc)
			worksheet.write('N6%s', 'ESI', boldc)
			worksheet.write('O6%s', 'LWF', boldc)
			worksheet.write('P6%s', 'Other Deductions', boldc)
			worksheet.write('Q6%s', 'Total Deductions', boldc)
			worksheet.merge_range('R5:R6', 'Salary Paid' , merge_format)
			worksheet.merge_range('S5:S6', 'Date of Payment' , merge_format)
			worksheet.merge_range('T5:T6', 'Signature or Thumb Impression of Employee' , merge_format)
			employee_id = False
			i = 0
			for rec in self.env['hr.payslip'].search([('company_id','=',register.company_id.id),('payslip_run_id','=',register.id)]): 
				for line in self.env['hr.payslip.line'].search(['|',('code','=','EPF'),('code','=','ENPFC'),('slip_id','=',rec.id)]): 
						# raise UserError(str(var.amount))
					if line.total != 0:
						if employee_id != line.slip_id.employee_id.id:
							employee_id = line.slip_id.employee_id.id
							new_row+=1
							
							i+=1
							worksheet.write('A%s' %(new_row), i)		
							worksheet.write('B%s' %(new_row), line.employee_id.name)
							worksheet.write('C%s' %(new_row), line.employee_id.job_id.name)
							# worksheet.write('E%s' %(new_row), rec.amount_total)
							worksheet.write('D%s' %(new_row), rec.contract_id.wage)
							worksheet.write('E%s' %(new_row), rec.contract_id.dearness_allowance)
							worksheet.write('R%s' %(new_row), rec.amount_total)
							worksheet.write('S%s' %(new_row), rec.date_from)
							for var in rec.line_ids:
								if var.code == 'BASIC':
									worksheet.write('F%s' %(new_row), var.total)
								if var.code == 'DA':
									worksheet.write('G%s' %(new_row), var.total)
								if var.code == 'SA':
									worksheet.write('J%s' %(new_row), var.total)
								if var.code == 'GROSS':
									worksheet.write('K%s' %(new_row), var.total)
								if var.code == 'EPF':
									worksheet.write('M%s' %(new_row), var.total)
									pf = var.total
								if var.code == 'ENPFC':
									worksheet.write('N%s' %(new_row), var.total)
									esi = var.total
								if var.code == 'LWF':
									worksheet.write('O%s' %(new_row), var.total)
									lwf = var.total
								if var.code == 'TED':
									worksheet.write('Q%s' %(new_row), var.total)
									total = var.total
									otherdeduction = round(total-pf-esi-lwf)
								

							worksheet.write('P%s' %(new_row), otherdeduction)

							for worked in rec.worked_days_line_ids:
									if worked.code =='WORK100':
									   worksheet.write('H%s' %(new_row), worked.number_of_days)
									if worked.code =='OT100':
									   worksheet.write('I%s' %(new_row), worked.number_of_days)
				

								
							
				



BiWagesXlsx('report.account.bi.wages.rep.xlsx','hr.payslip.run')