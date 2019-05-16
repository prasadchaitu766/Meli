from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import xlsxwriter
import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
import odoo.addons.decimal_precision as dp
import re
import string
from odoo.exceptions import UserError

class BiEmployeeLedgerXlsx(ReportXlsx):
	def generate_xlsx_report(self, workbook, data, invoices):

		invoice_obj = self.env['check.date'].search([])[-1]
		worksheet = workbook.add_worksheet(invoice_obj.company_id.name)

		for result in invoice_obj:
			boldc = workbook.add_format({'bold': True,'align': 'center'})
			bold = workbook.add_format({'bold': True})
			right = workbook.add_format({'align': 'right'})
			merge_format = workbook.add_format({
			'bold': 1,
			'border': 1,
			'align': 'center',
			'valign': 'vcenter',
			'bg_color': '#D3D3D3',
			'font_color': '#000000',
			})
			format_hidden = workbook.add_format({
			'hidden': True
			})
			align_format = workbook.add_format({
			'align': 'right',
			})
			row = 1
			col = 0
			new_row = row + 1
			y = 'Yes'
			n = 'No'

			worksheet.write('A%s' %(row), 'Month', merge_format)
			worksheet.write('B%s' %(row), 'Basic', merge_format)
			worksheet.write('C%s' %(row), 'OT', merge_format)
			worksheet.write('D%s' %(row), 'Leave Encashment', merge_format)
			worksheet.write('E%s' %(row), 'Total Allowance', merge_format)
			worksheet.write('F%s' %(row), 'Total Deduction', merge_format)
			worksheet.write('G%s' %(row), 'Net Pay', merge_format)
			employee_id = False
			var = []
			query = """SELECT hrc.name,hpl.company_id, sum(hpl.amount) AS amount,sum(hp.amount_total) AS amount_total 
						FROM hr_payslip hp
						INNER JOIN hr_payslip_line hpl ON hp.id=hpl.slip_id
						INNER JOIN hr_salary_rule_category hrc ON hpl.category_id=hrc.id

						where date_from<=%s and date_to>=%s 
						group by hpl.company_id,hrc.id
					"""
			self.env.cr.execute(query,(result.start_date,result.end_date))
			var = self.env.cr.dictfetchall()
			raise UserError(str(var[0]['amount_total']))
			

	
			for line in self.env['hr.payslip'].search([('date_from','>=',result.start_date),('date_to','<=',result.end_date),('company_id','=',result.company_id.id)]):
				for res in self.env['hr.payslip.line'].search([('slip_id','=',line.id)]): 
					if employee_id != res.slip_id.employee_id.id:
						employee_id = res.slip_id.employee_id.id

						
						worksheet.write('G%s' %(new_row), line.amount_total)
						worksheet.write('E%s' %(new_row), line.amount_allowance)
						worksheet.write('F%s' %(new_row), line.amount_deduction)
						for var in line.line_ids:
							if var.code == 'BASIC':
								worksheet.write('B%s' %(new_row), var.total)
							elif var.code == 'LE':
								worksheet.write('D%s' %(new_row), var.total)
						for worked in line.worked_days_line_ids:
							if worked.code =='OT100':
								worksheet.write('C%s' %(new_row), worked.number_of_days)

						# it works for geting month name between two dates.
						res = []
						start_date =  datetime.strptime(line.date_from,  '%Y-%m-%d')
						end_date = start_date + relativedelta(days=59)
						while start_date <= end_date:
							last_date = start_date + relativedelta(day=1, months=+1, days=-1)
							if last_date > end_date:
								last_date = end_date
							month_days = (last_date - start_date).days + 1
							res.append({'month_name': start_date.strftime('%B'), 'days': month_days})
							start_date += relativedelta(day=1, months=+1)
						
						worksheet.write('A%s' %(new_row), res[0]['month_name'])

						new_row+=1

						




BiEmployeeLedgerXlsx('report.account.bi.employee.ledger.xlsx','hr.payslip.run')
