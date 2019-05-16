from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
import xlsxwriter
import datetime
# from datetime import datetime, date
from datetime import datetime, timedelta, date
import odoo.addons.decimal_precision as dp
import re
import string
from odoo.exceptions import UserError

class BiMustrollXlsx(ReportXlsx):
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
			new_row = row + 7
			y = 'Yes'
			n = 'No'

			

			worksheet.merge_range('A1:AN1', 'Form VI' , merge_format)
			worksheet.merge_range('A2:AN2', '(Prescribed Under Rule 29(5))' , merge_format)
			worksheet.merge_range('A3:AN3', 'Register of Muster Roll for the Month of AUGUST 2017' , merge_format)
			worksheet.merge_range('A4:AN4', invoice_obj.company_id.name   , merge_format)
			worksheet.merge_range('A5:A7',  'SL.No', merge_format)
			worksheet.merge_range('B5:B7',  'Name of Worker', merge_format)
			worksheet.merge_range('C5:C7',  'Employee Code', merge_format)
			worksheet.merge_range('D5:D7',  'Designation or Nature of Work', merge_format)
			worksheet.merge_range('E5:E7',  'DATE OF JOINING', merge_format)
			worksheet.merge_range('F5:AJ7', invoice_obj.start_date    +'to'+   invoice_obj.end_date  , merge_format)
			worksheet.merge_range('AK5:AK7',  'No. of days worked', merge_format)
			worksheet.merge_range('AL5:AL7',  'No. of days of leave with wages', merge_format)
			worksheet.merge_range('AM5:AM7',  'No. of days absent', merge_format)
			worksheet.merge_range('AN5:AN7',  'No. of days counted for wages', merge_format)
			employee_id = False
			i = 0
			alpha = list(string.ascii_uppercase)
			for alp in range(0,26):
				alpha.append('A'+str(alpha[alp]))

			date_from = datetime.strptime(invoice_obj.start_date, '%Y-%m-%d')
			date_to = datetime.strptime(invoice_obj.end_date, '%Y-%m-%d')
			delta = date_to - date_from
			delta=(delta.days + 1)
			for datelist in range (delta):
				date = date_from + timedelta(days=datelist)
				date1 =date.day
				worksheet.write(alpha[datelist+5]+'%s' %(new_row), date1)
				
	 
			for line in self.env['hr.employee'].search([('company_id','=',result.company_id.id)]):
				payslip= self.env['hr.payslip'].search([('employee_id','=',line.id)],limit=1)
				for payslip_line in self.env['hr.payslip.line'].search(['|',('code','=','EPF'),('code','=','ENPFC'),('slip_id','=',payslip.id)]):
					if payslip_line.total!=0:
						attendance=self.env['hr.attendance'].search([('att_date','>=',result.start_date),('att_date','<=',result.end_date),('company_id','=',line.company_id.id),('employee_id','=',line.id)],order="employee_id")
						if not attendance:
							continue
						if employee_id != payslip_line.slip_id.employee_id.id:
							new_row+=1
							i+=1							
							worksheet.write('A%s' %(new_row), i)		
							worksheet.write('B%s' %(new_row), line.name)
							worksheet.write('C%s' %(new_row), line.code)
							worksheet.write('D%s' %(new_row), line.job_id.name)
							worksheet.write('E%s' %(new_row), line.date_of_join)
							employee_id = payslip_line.slip_id.employee_id.id	
						inc = 5
						count = 0
						count_a= 0	
						count_hp= 0
						count_wage= 0
						for datelist in range (delta):
							date = date_from + timedelta(days=datelist)
							attendance=self.env['hr.attendance'].search([('att_date','=',date),('company_id','=',line.company_id.id),('employee_id','=',line.id)],order="employee_id")
							
							if attendance:
								for rec in attendance:
									if rec.att_status=='Present':
										var='X'
										count = count+1		 						
									elif rec.att_status=='Absent':
										var='a'
										count_a = count_a+1		
									elif rec.att_status=='1/2Present':
										var='0.5'
										count= count+0.5
										count_a = count_a+0.5
									count_wage = count+4
									if count_a==0:
										worksheet.write('AL%s' %(new_row), '0', align_format)
										worksheet.write('AM%s' %(new_row), count_a) 
									elif count_a==0.5:
										worksheet.write('AL%s' %(new_row), '0.5', align_format)
										worksheet.write('AM%s' %(new_row), count_a-0.5) 
									else:
										worksheet.write('AL%s' %(new_row), '1', align_format)
										worksheet.write('AM%s' %(new_row), count_a-1) 


								
									worksheet.write('AK%s' %(new_row), count) 
									worksheet.write('AN%s' %(new_row), count_wage) 
									worksheet.write(alpha[inc]+'%s' %(new_row), var, align_format)
									inc = inc+1	



										
							else:
								if date.weekday()==6:
									worksheet.write(alpha[inc]+'%s' %(new_row), 'SUNDAY')
									inc = inc+1	
								else:
									worksheet.write(alpha[inc]+'%s' %(new_row), 'Nil', align_format)
									inc = inc+1	
							# holiday=self.env['hr.holidays'].search([('employee_id','=',line.id)],order="employee_id")
							# for hol in holiday:

					
											
BiMustrollXlsx('report.account.bi.mustroll.xlsx','hr.attendance')