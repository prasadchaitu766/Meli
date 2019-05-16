from openerp import api, fields, models, _
from odoo.exceptions import UserError, AccessError  
from datetime import datetime, timedelta
from datetime import date, datetime
import dateutil.parser
import urllib2
import json
import pytz

class BiQueueManagement(models.Model):
	_name = 'bi.queue.management'

	name = fields.Char("Name")
	token_id = fields.One2many('bi.token.management', 'department_id', "Token")
	no_token_employee = fields.Integer("Tokens Issued")
	counter_id = fields.Many2one('counter.master', "Counter")	

	@api.multi
	def close_dialog(self):
		return {'type': 'ir.actions.act_window_close'}


class BiTokenManagement(models.Model):
	_name = 'bi.token.management'

	department_id = fields.Many2one("bi.queue.management", "Department")
	user_id = fields.Many2one('res.users', "User", default=lambda self: self.env.user)
	name = fields.Char("Name")
	phone = fields.Char("Phone Number")
	date = fields.Date("Date", default=lambda self: fields.Datetime.now())
	pid = fields.Char('Token No', required=True,
					  default=lambda self: _('New'),
					  help='Personal IDentification Number')
	counter_id = fields.Many2one('counter.master', string="Counter")
	state = fields.Selection([('draft', 'Draft'), ('generate', 'Generate'), ('process', 'Processing'), ('close', 'Close')], index='true', default='draft')
	# video_id = fields.Many2one('youtube.video.link', "Youtube")

	@api.multi
	def generate_token(self):
		date_today= self.date
		token_obj=self.env['bi.token.management']
		date=datetime.today().strftime("%Y-%m-%d")
		app_no=token_obj.search([('date','=',date_today),('department_id','=',self.department_id.id),('state','!=','draft')],count=True)	
		self.pid = str(app_no+1) or _('New')
		self.write({'state':'generate'})
		token = self.env['bi.queue.management'].search([('id','=',self.department_id.id)])
		token.write({'no_token_employee':self.pid})
		# r-eturn {
  #           'type': 'ir.actions.act_window',
  #           'name': 'Token',
  #           'view_type': 'form',
  #           'view_mode': 'form',
  #           'res_model': 'bi.token.management',
  #           'target' : 'inline',
  #           'flags': {'initial_mode': 'edit'}
  #       }


		# return {'target':'inline'}


	@api.multi
	def print_token(self):
		""" Print the invoice and mark it as sent, so that we can see more
			easily the next step of the workflow
		"""
		current_time= datetime.now()
		current_time=current_time.strftime('%Y-%m-%d %I:%M %p')
		user_tz = self.user_id.tz or pytz.utc
		local = pytz.timezone(user_tz)
		current_time = datetime.strftime(pytz.utc.localize(datetime.strptime(str(current_time),"%Y-%m-%d %I:%M %p")).astimezone(local),"%d-%m-%Y %I:%M %p") 
		self.ensure_one()
		self.sent = True
		address = self.env['ip.address.setting'].search([])
		url = 'http://'+address.ip_address+':'+address.port_no+'/hw_proxy/print_xml_receipt'
		data = {
				"jsonrpc": "2.0",
				"params": {"receipt": u'<receipt align="center" font="a" value-thousands-separator="," width="30"><h3>'+self.user_id.company_id.name+'</h3><div>--------------------------------</div><p align="center">Date:'+current_time+'</p><br/><p>Your Token no is generated successfully!!</p><br/><p>Token No:</p><h1>'+self.pid+'</h1><br/><br/><div>--------------------------------</div><p align="left">Please take your seat,we will attain you soon!!</p><div font="a"><br/>' + \
										u'</div></receipt>'},
			}
		req = urllib2.Request(url,json.dumps(data), headers={"Content-Type":"application/json",})
		result = urllib2.urlopen(req)
		# action = self.env.ref('bi_queue_management.action_token_management_tree')
		# result = action.read()[0]
		# res = self.env.ref('bi_queue_management.bi_token_management_form', False)
		# result['views'] = [(res and res.id or False, 'form')]
		# return result

		# context ={
		# 		  'default_name':'',
		# 		  'default_phone':'',
		# 		}
		# return {
		# 		'type': 'ir.actions.act_window',
		# 		'res_model': 'bi.token.management',
		# 		'target' : 'inline',
		# 		'view_mode':'form',
		# 		}
		



	@api.multi
	def set_start(self):
		self.write({'state':'process'})

	@api.multi
	def set_close(self):
		self.write({'state':'close'})


class IpAddressSetting(models.Model):
	_name = 'ip.address.setting'
	_rec_name = 'ip_address'

	ip_address = fields.Char("Ip Address")
	port_no = fields.Char("Port Number")

	@api.model
	def create(self, vals):
		address = self.env['ip.address.setting'].search([])
		if address:
			raise UserError('Please Update the current Ip address and Port Number')
		result = super(IpAddressSetting, self).create(vals)	
		return result	

class YoutubeVideoLink(models.Model):
	_name = 'youtube.video.link'
	_rec_name = 'video_link'

	video_link = fields.Char("Video Link")
	

class CounterMaster(models.Model):
	_name = 'counter.master'

	queue_id = fields.One2many('bi.queue.management','counter_id')
	name = fields.Char("Counter Name")
	user_id = fields.Many2one('res.users', string="Owner")