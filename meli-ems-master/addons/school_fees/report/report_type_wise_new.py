import time
from odoo import api, models
from odoo.exceptions import UserError
from datetime import datetime, timedelta, date
from dateutil import relativedelta
from itertools import groupby
from operator import itemgetter
from dateutil import parser
import itertools


class FeesTypeReport(models.Model):
	_name = 'report.school_fees.type_wise'


	def get_lines(self, data):
		lines = []	
		line_ids = []	
		vals = {
			'sem':'',
			'name':'',
			# 'qty':'',
			'exam':'',
			'lateexam':'',
			'code': '',
			'disamount':'', 
			'rfdamount': '',
			# 'campus':'',
			'book':'',
			'repeat':'',
			'total':0.0,
			'card':'',
			'other':'',
		}
		end_date=data['form']['end_date']
		start_date=data['form']['start_date']
		domain=[('slip_id.date', '>=', data['form']['start_date']),
				('slip_id.date', '<=', data['form']['end_date']),('slip_id.state', '=', 'paid')]
		
		if data['form']['school_id']:
			domain.append(('slip_id.school_id','=',data['form']['school_id'][0]))
			# campus_obj = self.env['school.school'].search([('id','=',data['form']['school_id'][0])])
		if data['form']['fees_id']:
			domain.append(('name','=',data['form']['fees_id'][1]))
		if data['form']['semester_id']:
			domain.append(('slip_id.student_id.semester_id','=',data['form']['semester_id'][0]))
		# refund=self.env['student.payslip'].search(domain)
		# raise UserError(str(refund))
		student_obj = self.env['student.payslip.line'].search(domain)
		for line in student_obj:
			# if data['form']['school_id']:
			# 	campus1 = campus_obj
			# for structure in line.slip_id.fees_structure_id.line_ids:
			if line.fee_type == 'tuitionfee':
				tuition_fee =line.amount
			else:
				tuition_fee = 0.0
			if line.fee_type == 'book':
				price =line.amount
			else:
				price = 0.0
			if line.fee_type == 'idcard':
				card_price = line.amount
			else:
				card_price = 0.0
			if line.fee_type == 'other':
				other_price = line.amount
			else:
				other_price = 0.0
			if line.fee_type == 'repeat':
				repeat_amount = line.amount
			else:
				repeat_amount = 0.0
			if line.fee_type == 'exam':
				exam_amount = line.amount
			else:
				exam_amount = 0.0
			if line.fee_type == 'lateexam':
				lateexam_amount = line.amount
			else:
				lateexam_amount = 0.0
				# if line.slip_id.refund_amount:
				# 	rfd_amount = refund_amount
				# else:
				# 	rfd_amount = 0.0
			vals = {
				'slip_id':line.slip_id.id,
				'sem':line.slip_id.fees_structure_id.semester_id.name,
				'name': line.name,
				# 'product': line.product_id.name,
				'code': line.code,
				'disamount': line.amount-line.price_subtotal,
				'tuitionfee': tuition_fee,
				'exam': exam_amount,
				'lateexam': lateexam_amount,
				# 'total': line.price_subtotal,
				# 'amt': line.amount,
				# 'campus': campus1,
				'book': price,
				'idcard': card_price,
				'other': other_price,
				'repeat': repeat_amount,
				'rfdamount':line.slip_id.refund_amount
			}
			lines.append(vals)

		line1 = sorted(lines, key=itemgetter('sem'))
		for key, value in itertools.groupby(line1, key=itemgetter('sem')):
			amount = discount = qnty = bookprice = examamt = lateexamamt = rptamount = rfamount = cardprice = otherprice = tuitionamount = 0.0    
			rpam = {}
			for item in list(value):
				# amount+=float(item['total'])
				tuitionamount+=float(item['tuitionfee'])
			
				discount+=float(item['disamount'])
				# qnty+=float(item['qty'])
				examamt+=float(item['exam'])
				lateexamamt+=float(item['lateexam'])
				bookprice+=float(item['book'])
				rptamount+=float(item['repeat'])
				cardprice+=float(item['idcard'])
				otherprice+=float(item['other'])
				if item['slip_id'] not in rpam:
					rpam[item['slip_id']] = float(item['rfdamount'])
			refund_sum = sum(rpam[item] for item in rpam)
			line_ids.append({'sem': item['sem'],'name': item['name'], 'code': item['code'], 'amount':tuitionamount+cardprice+bookprice, 'discount':discount, 'qnty':qnty, 'examamt':examamt, 'lateexamamt':lateexamamt, 'bookprice':bookprice, 'rptamount':rptamount, 'total':tuitionamount+otherprice+cardprice+bookprice+lateexamamt+examamt+rptamount-discount-refund_sum, 'cardprice':cardprice, 'otherprice':otherprice, 'rfamount':refund_sum , 'tuitionamount':tuitionamount})
		return line_ids
			


	@api.model
	def render_html(self, docids, data=None):
		self.model = self.env.context.get('active_model')
		docs = self.env[self.model].browse(self.env.context.get('active_ids', []))
		type_det = {}
		type_det = self.get_lines(data)
		docargs = {
			'doc_ids': self.ids,
			'doc_model': self.model,
			'data': data['form'],
			'docs': docs,
			'time': time,
			'line_ids': type_det,
		}
		return self.env['report'].render('school_fees.type_wise', docargs)