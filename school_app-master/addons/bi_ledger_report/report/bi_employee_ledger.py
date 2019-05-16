from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import xlsxwriter
import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta, date
import odoo.addons.decimal_precision as dp
import re
import string
from odoo.exceptions import UserError
from collections import defaultdict
from dateutil import parser

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
			new_row = row 
			y = 'Yes'
			n = 'No'

			worksheet.write('A%s' %(row), 'Month', merge_format)
			worksheet.write('B%s' %(row), 'Basic', merge_format)
			worksheet.write('C%s' %(row), 'OT', merge_format)
			# worksheet.write('D%s' %(row), 'Leave Encashment', merge_format)
			worksheet.write('D%s' %(row), 'Total Allowance', merge_format)
			worksheet.write('E%s' %(row), 'Total Deduction', merge_format)
			worksheet.write('F%s' %(row), 'Net Pay', merge_format)
			
			payslips = []
			query = """SELECT  hp.date_from,hrc.name,hp.company_id, sum(hpl.amount) AS amount,
					  (SELECT sum(hp1.amount_total) as amount_total FROM hr_payslip hp1  
					  where hp1.date_from =hp.date_from and hp1.state='done' and hp1.company_id=hp.company_id) as amount_total,
		              (SELECT max(hpw.number_of_days) AS ot FROM hr_payslip hp1
					  INNER JOIN hr_payslip_worked_days hpw ON hpw.payslip_id=hp1.id
					  WHERE  hp1.date_from =hp.date_from and hp1.state='done' and hp1.company_id=hp.company_id AND hpw.code='OT100') AS ot	
					  FROM hr_payslip hp
					  INNER JOIN hr_payslip_line hpl ON hp.id=hpl.slip_id
					  INNER JOIN hr_salary_rule_category hrc ON hpl.category_id=hrc.id				
					  WHERE hp.date_from>=%s AND hp.date_to<=%s AND hp.state='done' AND hp.company_id=%s
					  group by hp.company_id,hrc.id,hp.date_from order by hp.date_from
					"""
			self.env.cr.execute(query,(result.start_date,result.end_date,result.company_id.id))
			payslips = self.env.cr.dictfetchall()
			
			amount_total = 0.0
			ot = 0.0
			st_date = False
			for line in payslips:
				if st_date != line['date_from']:
						
					st_date = line['date_from']
					if amount_total> 0.0:
						worksheet.write('F%s' %(new_row), amount_total)
					if ot> 0.0:
						worksheet.write('C%s' %(new_row), ot)
					new_row+=1
					worksheet.write('A%s' %(new_row),datetime.strptime(line['date_from'],  '%Y-%m-%d').strftime("%B-%Y"))					
					amount_total = line['amount_total']
					ot = line['ot']

				if line['name'] == 'Basic':
					worksheet.write('B%s' %(new_row), line['amount'])
				if line['name'] == 'Allowance':
					worksheet.write('D%s' %(new_row), line['amount'])
				if line['name'] == 'Deduction':
					worksheet.write('E%s' %(new_row), line['amount'])
			if ot> 0.0:
				worksheet.write('C%s' %(new_row), ot)

			if amount_total> 0.0:
				worksheet.write('F%s' %(new_row), amount_total)
						




BiEmployeeLedgerXlsx('report.account.bi.employee.ledger.xlsx','hr.payslip.run')
