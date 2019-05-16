# -*- coding: utf-8 -*-
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import xlsxwriter
import datetime
from datetime import datetime, date
import odoo.addons.decimal_precision as dp
import re
class ExcelPayslipXlsx(ReportXlsx):
	def generate_xlsx_report(self, workbook, data, invoices):
		invoice_obj = self.env['payslip.lines.contribution.register'].search([])[-1]
		register_ids = self.env.context.get('active_ids', [])
		contrib_registers = self.env['hr.contribution.register'].browse(register_ids)
		for register in contrib_registers:
			date_from =invoice_obj.date_from
			date_to =  invoice_obj.date_to
			employee_id = invoice_obj.employee_id.id
			result = {}
			self.env.cr.execute("""
				SELECT pl.id from hr_payslip_line as pl
				LEFT JOIN hr_payslip AS hp on (pl.slip_id = hp.id)
				WHERE (hp.date_from >= %s) AND (hp.date_to <= %s)
				AND pl.register_id = %s
				AND hp.state = 'done' """ + (employee_id and " and hp.employee_id = " +str(employee_id) or "")+""" 
				ORDER BY pl.slip_id, pl.sequence""",
				(date_from, date_to, register.id))
			line_ids = [x[0] for x in self.env.cr.fetchall()]
			
			worksheet = workbook.add_worksheet(register.name)
			worksheet.set_column('A:K',15)

			row = 1
			col = 0
			new_row = row + 1
			y = 'Yes'
			n = 'No'
			format = workbook.add_format({'bold': True, 'bg_color': 'cccccc'})
			for rec in self.env['hr.payslip.line'].browse(line_ids): 
				worksheet.write('A%s' %(row), rec.name + "  " + "From" ,format)
			worksheet.write('B%s' %(row), date_from,format)
			worksheet.write('C%s' %(row), 'To',format)
			worksheet.write('D%s' %(row), date_to,format)
			row = row + 1
			format = workbook.add_format({'bold': True, 'font_color': '996600'})
			worksheet.write('A%s' %(row), 'PaySlip Name',format)
			worksheet.write('B%s' %(row), 'Employee Name',format)
			worksheet.write('C%s' %(row), 'Amount',format)
			new_row = row + 1
			ls = []

			for line in self.env['hr.payslip.line'].browse(line_ids):   
					   
						worksheet.write('A%s' %(new_row), line.slip_id.name)
						worksheet.write('B%s' %(new_row), line.slip_id.employee_id.name)
						worksheet.write('C%s' %(new_row), line.amount)
						

						new_row+=1



ExcelPayslipXlsx('report.bi_hr_tp.excel.payslip.xlsx','hr.contribution.register')











