# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
# Please see LICENSE file.
#################################################################################
import logging
import odoo
import re
import pytz
import time
from datetime import datetime, timedelta
import werkzeug.utils
import hashlib
from odoo import http
from odoo.http import request
import json
_logger = logging.getLogger(__name__)
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
import math

class PosMirrorController_2(http.Controller):
	@http.route('/campus/student_data', type='http', auth='user',website=True)
	def mirror_data(self,**k):
		cr, uid, context, session = request.cr, request.uid, request.context, request.session
		time_table_obj = request.env['time.table']
		time_table_line_obj=request.env['time.table.line']
		notif_obj = request.env['bi.notification.msg']
		notification_id = notif_obj.search([('create_note','=',uid)])
		order_list = []
		photo_list = []
		status_list = []
		stu_id_list = []
		class_list = []
		teacher_list = []
		shift_list = []
		campus_list = []
		date_list = []
		subject_list = []
		teacher_photo_list = []
		shift_to =[]
		shift_from =[]


		if notification_id:
			notification_id[0].write({'msg':True})
		session_name = []
		time_from_formated=0.0
		time_to_formated=0.0
		

		if session.has_key('session_link'):
			session_name = session['session_link']
			date_today=datetime.today().strftime('%Y-%m-%d')
			timtable_data = time_table_obj.search([])
			current_time= datetime.now()
			current_time=current_time.strftime('%H.%M')
			user=request.env['res.users'].search([('id','=',uid)])
			user_tz = user.tz or pytz.utc
			local = pytz.timezone(user_tz)
			current_time = datetime.strftime(pytz.utc.localize(datetime.strptime(str(current_time),"%H.%M")).astimezone(local),"%H.%M") 
			for data in timtable_data:
				medium_id=data.medium_id
				time_from=medium_id.hour_from
				time_to=medium_id.hour_to
				if  float(current_time) < time_to and  float(current_time) > time_from:
					current_day=datetime.today().weekday()
					if current_day == 0:
						domain = [
							  ('table_id', '=', data.id),
							  ('week_day', '=', 'monday'),
						  ]
					elif current_day == 1:
						domain = [
							  ('table_id', '=', data.id),
							  ('week_day', '=', 'tuesday'),
						  ]
					elif current_day == 2:
						domain = [
							('table_id', '=', data.id),
							('week_day', '=', 'wednesday'),
						  ]
					elif current_day == 3:
						domain = [
							  ('table_id', '=', data.id),
							  ('week_day', '=', 'thursday'),
						  ]
					elif current_day == 4:
						domain = [
							  ('table_id', '=', data.id),
							  ('week_day', '=', 'friday'),
						  ]
					elif current_day == 5:
						domain = [
							  ('table_id', '=', data.id),
							  ('week_day', '=', 'saturday'),
						  ]
					else:
						domain = [
							  ('table_id', '=', data.id),
							  ('week_day', '=', 'sunday'),
						  ]

					time_table_line_id=request.env['time.table.line'].search(domain,limit=1)
					teacher_list.append(time_table_line_id.teacher_id.name or '-') 
					subject_list.append(time_table_line_id.subject_id.name or '-')
					shift_list.append(medium_id.name)
					shift_from.append(time_from)
					shift_to.append(time_to)
					class_list.append(data.standard_id.name)
					campus_list.append(data.school_id.name)
			return json.dumps({'shift_list':eval(str(shift_list)),'teacher_list':eval(str(teacher_list)),'class_list':eval(str(class_list)),'campus_list':eval(str(campus_list)),'subject_list':eval(str(subject_list)),'shift_from':eval(str(shift_from)),'shift_to':eval(str(shift_to))})
		return request.redirect("/campus/student")

	def convert_float_time(self,time_data):
		frac, whole = math.modf(time_data)
		frac_min=((frac* 60)/100)
		hr=whole
		if frac_min>59:
			hr=whole+1
			frac_min=frac_min-59
		data=hr+frac_min
		return data


	def longPooling(self, cr, uid, session_name,database_name):
		registry = openerp.registry(database_name)
		timeout_ago = datetime.datetime.utcnow()-datetime.timedelta(seconds=TIMEOUT)
		notif_obj = request.registry['bi.notification.msg']
		notification_id = notif_obj.search(cr,uid,[('create_note','=',uid)])
		cr.execute("SELECT create_date FROM daily_attendance_line where id = %s" %(session_name))
		result = cr.dictfetchall()
		check_date = result[0]['create_date'] > timeout_ago.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		while not check_date:
			time.sleep(2)
			notif_obj.write(cr,uid,notification_id,{'msg':True})
			with registry.cursor() as cr:
				timeout_ago = datetime.datetime.utcnow()-datetime.timedelta(seconds=TIMEOUT)
				cr.execute("SELECT create_date FROM daily_attendance_line where id = %s"%(session_name))
				result = cr.dictfetchall()
				check_date = result[0]['create_date'] > timeout_ago.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		if check_date:
			notif_obj.write(cr,uid,notification_id,{'msg':True})

	@http.route('/campus/student', type='http', auth='user',website=True)
	def mirror(self, debug=False, **k):
		cr, uid, context, session = request.cr, request.uid, request.context, request.session
		mirror_img = request.env['daily.attendance']        
		mirror_img_ids = mirror_img.search([])
		if mirror_img_ids:          
			image_data = []
			first_img = {}
			vals ={}
			session['session_link'] = mirror_img_ids[0].id          
			return request.render('bi_campus_screen.index1', vals)
		else:
			return "<h1>Link is Not valid.....</h1>"

	def image_url(self, cr, uid, record, field, size=None, context=None):
		"""Returns a local url that points to the image field of a given browse record."""
		sudo_record = record
		sha = hashlib.sha1(getattr(sudo_record, '__last_update')).hexdigest()[0:7]
		size = '' if size is None else '/%s' % size
		return '/web/image/%s/%s/%s%s?unique=%s' % (record._name, record.id, field, size, sha)



