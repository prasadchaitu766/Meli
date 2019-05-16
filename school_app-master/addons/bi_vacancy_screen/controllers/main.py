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

class PosMirrorController_3(http.Controller):
	@http.route('/campus/class_data', type='http', auth='user',website=True)
	def mirror_data(self,**k):
		cr, uid, context, session = request.cr, request.uid, request.context, request.session
		standard_obj = request.env['school.standard']
		notif_obj = request.env['bi.notification.msg']
		notification_id = notif_obj.search([('create_note','=',uid)])
		class_list = []
		shift_list = []
		campus_list = []
		shift_to =[]
		shift_from =[]
		vacancy_list = []
		semester_list=[]
		if notification_id:
			notification_id[0].write({'msg':True})
		session_name = []
		time_from_formated=0.0
		time_to_formated=0.0
		

		if session.has_key('session_link'):
			session_name = session['session_link']
			date_today=datetime.today().strftime('%Y-%m-%d')
			class_data = standard_obj.search([])
			current_time= datetime.now()
			current_time=current_time.strftime('%H.%M')
			user=request.env['res.users'].search([('id','=',uid)])
			user_tz = user.tz or pytz.utc
			local = pytz.timezone(user_tz)
			current_time = datetime.strftime(pytz.utc.localize(datetime.strptime(str(current_time),"%H.%M")).astimezone(local),"%H.%M") 
			for data in class_data:
				medium_id=data.medium_id
				time_from=medium_id.hour_from
				time_from=self.convert_float_time(time_from)
				time_to=medium_id.hour_to	
				time_to=self.convert_float_time(time_to)		
				if  float(current_time) < (time_to) and  float(current_time) > (time_from):
					shift_list.append(medium_id.name)
					shift_from.append(time_from)
					shift_to.append(time_to)
					class_list.append(data.standard_id.name)
					campus_list.append(data.school_id.name)
					vacancy_list.append(data.remaining_seats)
					semester_list.append(data.semester_id.name)
			return json.dumps({'shift_list':eval(str(shift_list)),'class_list':eval(str(class_list)),'campus_list':eval(str(campus_list)),'shift_from':eval(str(shift_from)),'shift_to':eval(str(shift_to)),'vacancy_list':eval(str(vacancy_list)),'semester_list':eval(str(semester_list))})
		return request.redirect("/campus/class")

	def convert_float_time(self,time_data):
		frac, whole = math.modf(time_data)
		frac_min=((frac* 60)/100)
		hr=whole
		if frac_min>59:
			hr=whole+1
			frac_min=frac_min-59
		data=hr+frac_min
		# c= open("/home/bassam5/error.txt", "a")
		# c.write(str(data)+'data\n')
		# c.close()
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

	@http.route('/campus/class', type='http', auth='user',website=True)
	def mirror(self, debug=False, **k):
		cr, uid, context, session = request.cr, request.uid, request.context, request.session
		mirror_img = request.env['daily.attendance']        
		mirror_img_ids = mirror_img.search([])
		if mirror_img_ids:          
			image_data = []
			first_img = {}
			vals ={}
			session['session_link'] = mirror_img_ids[0].id          
			return request.render('bi_vacancy_screen.index1', vals)
		else:
			return "<h1>Link is Not valid.....</h1>"

	def image_url(self, cr, uid, record, field, size=None, context=None):
		"""Returns a local url that points to the image field of a given browse record."""
		sudo_record = record
		sha = hashlib.sha1(getattr(sudo_record, '__last_update')).hexdigest()[0:7]
		size = '' if size is None else '/%s' % size
		return '/web/image/%s/%s/%s%s?unique=%s' % (record._name, record.id, field, size, sha)