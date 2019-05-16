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

class TokenMirrorController(http.Controller):
	@http.route('/class/token_data', type='http', auth='user',website=True)
	def mirror_data(self,**k):
		cr, uid, context, session = request.cr, request.uid, request.context, request.session
		queue_details = request.env['bi.queue.management']
		token_details=request.env['bi.token.management']
		video_details=request.env['youtube.video.link']
		dpt = token_details.department_id.id
		notif_obj = request.env['bi.notification.msg']
		notification_id = notif_obj.search([('create_note','=',uid)])
		token_list = []
		counter_list = []
		user_list = []
		depart_list = []
		date_list = []
		video_list = []

		if notification_id:
			notification_id[0].write({'msg':True})
		session_name = []
		time_from_formated=0.0
		time_to_formated=0.0


		if session.has_key('session_link'):
			session_name = session['session_link']
			date_today=datetime.today().strftime('%Y-%m-%d')
			token = token_details.search([('date','=',date_today),('state','=','process')])
			video = video_details.search([])
			for vid in video:
				video_list.append(vid.video_link)
				
			# current_time= datetime.now()
			# current_time=current_time.strftime('%Y-%m-%d %I:%M %p')
			# user_tz = self.user_id.tz or pytz.utc
			# local = pytz.timezone(user_tz)
			# current_time = datetime.strftime(pytz.utc.localize(datetime.strptime(str(current_time),"%Y-%m-%d %I:%M %p")).astimezone(local),"%d-%m-%Y %I:%M %p") 
			# current_time = datetime.strftime(pytz.utc.localize(datetime.strptime(str(current_time),"%H.%M")).astimezone(local),"%H.%M") 
			for line in token:
				token_list.append(line.pid)
				depart_list.append(line.department_id.name)
				user_list.append(line.name)
				hh=counter_list.append(line.department_id.counter_id.name)
				# video_list.append(line.video_id.video_link)
				# date_list.append(current_time)
				#   c= open("/home/bassam3/Desktop/error.txt", "a")
				# c.write(str(counter_list.append(line.department_id.counter_id.name)))
				# c.close()

			return json.dumps({'token':eval(str(token_list)),'department':eval(str(depart_list)),'user':eval(str(user_list)),'counter':eval(str(counter_list)),'video':eval(str(video_list))})
		return request.redirect("/class/token_data")

	# def convert_float_time(self,time_data):
	# 	frac, whole = math.modf(time_data)
	# 	frac_min=((frac* 60)/100)
	# 	hr=whole
	# 	if frac_min>59:
	# 		hr=whole+1
	# 		frac_min=frac_min-59
	# 	data=hr+frac_min
	# 	return data

	def longPooling(self, cr, uid, session_name,database_name):
		registry = openerp.registry(database_name)
		timeout_ago = datetime.datetime.utcnow()-datetime.timedelta(seconds=TIMEOUT)
		notif_obj = request.registry['bi.notification.msg']
		notification_id = notif_obj.search(cr,uid,[('create_note','=',uid)])
		cr.execute("SELECT create_date FROM bi_token_management where id = %s" %(session_name))
		result = cr.dictfetchall()
		check_date = result[0]['create_date'] > timeout_ago.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		while not check_date:
			time.sleep(2)
			notif_obj.write(cr,uid,notification_id,{'msg':True})
			with registry.cursor() as cr:
				timeout_ago = datetime.datetime.utcnow()-datetime.timedelta(seconds=TIMEOUT)
				cr.execute("SELECT create_date FROM bi_token_management where id = %s"%(session_name))
				result = cr.dictfetchall()
				check_date = result[0]['create_date'] > timeout_ago.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
		if check_date:
			notif_obj.write(cr,uid,notification_id,{'msg':True})

	@http.route('/class/token', type='http', auth='user',website=True)
	def mirror(self, debug=False, **k):
		cr, uid, context, session = request.cr, request.uid, request.context, request.session
		mirror_img = request.env['bi.token.management']        
		mirror_img_ids = mirror_img.search([])
		if mirror_img_ids:          
			image_data = []
			first_img = {}
			vals ={}
			session['session_link'] = mirror_img_ids[0].id          
			return request.render('bi_token_screen.index1', vals)
		else:
			return "<h1>Link is Not valid.....</h1>"

	def image_url(self, cr, uid, record, field, size=None, context=None):
		"""Returns a local url that points to the image field of a given browse record."""
		sudo_record = record
		sha = hashlib.sha1(getattr(sudo_record, '__last_update')).hexdigest()[0:7]
		size = '' if size is None else '/%s' % size
		return '/web/image/%s/%s/%s%s?unique=%s' % (record._name, record.id, field, size, sha)