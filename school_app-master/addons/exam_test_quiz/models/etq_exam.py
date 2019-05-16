import logging
_logger = logging.getLogger(__name__)
import requests
from odoo.http import request
from datetime import datetime,timedelta
from openerp.tools import html_escape as escape, ustr, image_resize_and_sharpen, image_save_for_web
import unicodedata
import pytz
import re
import time
import uuid
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models,_
from odoo import tools
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

class EtqExam(models.Model):

    _name = "etq.exam"
    
    name = fields.Char(string="Name", translate=True)
    slug = fields.Char(string="Slug", compute="slug_me", store="True")
    show_correct_questions = fields.Boolean(string="Show Correct Answers?")
    questions = fields.One2many('etq.question','exam_id', string="Questions")
    fill_mode = fields.Selection([('all','All Questions'),('random','Random')], string="Fill Mode", default="all")
    fill_mode_random_number = fields.Integer(string="Number of Random Questions")
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")
    start_tstring = fields.Char(string="Start Time")
    end_tstring = fields.Char(string="End Time")
    exam_id = fields.Many2one('exam.exam',string='Exam')
    exam_timetable_line_id = fields.Many2one('time.table.line', 'TimeTable')

    # hour_from = fields.Float('Start Time')
    # hour_to = fields.Float('End Time')
    # from_hour = fields.Char("Time From")
    # to_hour = fields.Char("Time To")
    # diff_hour = fields.Char("Diff Time")



    @api.onchange('start_time','end_time')
    def _onchange_time(self):
        start_time = ''
        end_time = ''
        user_tz = pytz.timezone(self.env.context.get('tz') or self.env.user.tz or 'UTC')
        
        if self.start_time:
            # start_time = str(self.start_time)
            # start_time2 = user_tz.localize(fields.Datetime.from_string(start_time))
            # start_time2 = start_time2.astimezone(pytz.timezone('UTC'))

            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(str(user_tz))
            start_time = datetime.strftime(pytz.utc.localize(datetime.strptime(
                self.start_time, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")

            # self.start_tstring = str(start_time)
            self.start_tstring = str(self.start_time)
        if self.end_time:
            # end_time = str(self.end_time)
            user_tz = self.env.user.tz or pytz.utc
            local = pytz.timezone(str(user_tz))
            end_time = datetime.strftime(pytz.utc.localize(datetime.strptime(
                self.end_time, DEFAULT_SERVER_DATETIME_FORMAT)).astimezone(local),"%Y-%m-%d %H:%M:%S")

            # self.end_tstring = str(end_time)
            self.end_tstring = str(self.end_time)

        # current_time = datetime.strptime(self.start_time,'%Y-%m-%d %H:%M:%S')
        # user_tz = self.env.user.tz or pytz.utc
        # local = pytz.timezone(user_tz)
        # current_time = datetime.strftime(
        # pytz.utc.localize(datetime.strptime(str(current_time), "%Y-%m-%d %H:%M:%S")).astimezone(local),
        #     "%Y-%m-%d %H:%M:%S")

    @api.onchange('fill_mode')
    def _onchange_fill_mode(self):
        if self.fill_mode == "random":
            self.fill_mode_random_number = len(self.questions)
    
    @api.multi
    def view_quiz(self):
        quiz_url = request.httprequest.host_url + "exam/" + str(self.slug)
        return {
                  'type'     : 'ir.actions.act_url',
                  'target'   : 'new',
                  'url'      : quiz_url
               } 
       
       
    @api.one
    @api.depends('name')
    def slug_me(self):
        if self.name:
            s = ustr(self.name)
            uni = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
            slug = re.sub('[\W_]', ' ', uni).strip().lower()
            slug = re.sub('[-\s]+', '-', slug)
            
            self.slug = slug
    
class EtqQuestion(models.Model):

    _name = "etq.question"
    _rec_name = "question"
    
    exam_id = fields.Many2one('etq.exam',string="Exam ID")
    exam_pre_id = fields.Many2one('etq.question.prepare',string="Exam Prepare")
    image = fields.Binary(string="Image")
    question = fields.Html(string="Question")
    question_rendered = fields.Html(string="Question Render", compute="render_question", sanitize=False)
    question_type = fields.Selection((('multi_choice','Multiple Choice'), ('fill_blank','Fill in the Blank'),), default="multi_choice", string="Question Type")
    question_options = fields.One2many('etq.question.option','question_id',string="Multiple Choice Options")
    question_options_blank = fields.One2many('etq.question.optionblank','question_id',string="Fill in the Blank Options")    
    num_options = fields.Integer(string="Options",compute="calc_options")
    num_correct = fields.Integer(string="Correct Options",compute="calc_correct")
    school_id = fields.Many2one('school.school', 'Campus',required = False) 
    subject_id = fields.Many2one("subject.subject", "Subject Name")
    semester_id = fields.Many2one('standard.semester', 'Semester')
    standard_id = fields.Many2one('standard.standard', 'Program')



    

    @api.one
    @api.depends('question')
    def render_question(self):
        if self.question:
            temp_string = self.question
            
            temp_string = temp_string.replace("{1}","<i><input name=\"question" + str(self.id) + "option1\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{2}","<i><input name=\"question" + str(self.id) + "option2\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{3}","<i><input name=\"question" + str(self.id) + "option3\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{4}","<i><input name=\"question" + str(self.id) + "option4\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{5}","<i><input name=\"question" + str(self.id) + "option5\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{6}","<i><input name=\"question" + str(self.id) + "option6\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{7}","<i><input name=\"question" + str(self.id) + "option7\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{8}","<i><input name=\"question" + str(self.id) + "option8\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{9}","<i><input name=\"question" + str(self.id) + "option9\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{10}","<i><input name=\"question" + str(self.id) + "option10\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{11}","<i><input name=\"question" + str(self.id) + "option11\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{12}","<i><input name=\"question" + str(self.id) + "option12\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{13}","<i><input name=\"question" + str(self.id) + "option13\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{14}","<i><input name=\"question" + str(self.id) + "option14\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{15}","<i><input name=\"question" + str(self.id) + "option15\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{16}","<i><input name=\"question" + str(self.id) + "option16\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{17}","<i><input name=\"question" + str(self.id) + "option17\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{18}","<i><input name=\"question" + str(self.id) + "option18\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{19}","<i><input name=\"question" + str(self.id) + "option19\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{20}","<i><input name=\"question" + str(self.id) + "option20\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{21}","<i><input name=\"question" + str(self.id) + "option21\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{22}","<i><input name=\"question" + str(self.id) + "option22\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{23}","<i><input name=\"question" + str(self.id) + "option23\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{24}","<i><input name=\"question" + str(self.id) + "option24\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{25}","<i><input name=\"question" + str(self.id) + "option25\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{26}","<i><input name=\"question" + str(self.id) + "option26\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{27}","<i><input name=\"question" + str(self.id) + "option27\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            self.question_rendered = temp_string
            
            

    @api.one
    @api.depends('question_options')
    def calc_options(self):
        self.num_options = self.question_options.search_count([('question_id','=',self.id)])
    
    @api.one
    @api.depends('question_options')
    def calc_correct(self):
        self.num_correct = self.question_options.search_count([('question_id','=',self.id), ('correct','=',True)])
    
class EtqQuestionOptions(models.Model):

    _name = "etq.question.option"
    _rec_name = "option"
    
    question_id = fields.Many2one('etq.question',string="Question ID")
    option = fields.Char(string="Option")
    correct = fields.Boolean(string="Correct")
    
class EtqQuestionOptionBlank(models.Model):

    _name = "etq.question.optionblank"
    
    question_id = fields.Many2one('etq.question',string="Question ID")
    answer = fields.Char(string="Blank Answer")

class EtqQuoPrepare(models.Model):

    _name = "etq.question.prepare"
    
    name = fields.Char(string="Name", translate=True,default='New')
    school_id = fields.Many2one('school.school', 'Campus',required = False) 
    subject_id = fields.Many2one("subject.subject", "Subject Name")
    semester_id = fields.Many2one('standard.semester', 'Semester')
    standard_id = fields.Many2one('standard.standard', 'Program')
    questions = fields.Many2many('etq.question.prepare.line', string="Questions")


class EtqQuestionPrepareLine(models.Model):
    _name = "etq.question.prepare.line"
    _rec_name = "question"

    # exam_id = fields.Many2one('etq.exam', string="Exam ID")
    exam_pre_id = fields.Many2one('etq.question.prepare', string="Exam Prepare")
    image = fields.Binary(string="Image")
    question = fields.Html(string="Question")
    question_rendered = fields.Html(string="Question Render", compute="render_question", sanitize=False)
    question_type = fields.Selection((('multi_choice', 'Multiple Choice'), ('fill_blank', 'Fill in the Blank'),), default="multi_choice",
                                     string="Question Type")
    question_options = fields.One2many('etq.question.prepare.line.option', 'question_id', string="Multiple Choice Options")
    question_options_blank = fields.One2many('etq.question.prepare.line.optionblank', 'question_id',
                                             string="Fill in the Blank Options")
    num_options = fields.Integer(string="Options", compute="calc_options")
    num_correct = fields.Integer(string="Correct Options", compute="calc_correct")
    school_id = fields.Many2one('school.school', 'Campus', required=False)
    subject_id = fields.Many2one("subject.subject", "Subject Name")
    semester_id = fields.Many2one('standard.semester', 'Semester')
    standard_id = fields.Many2one('standard.standard', 'Program')

    @api.one
    @api.depends('question')
    def render_question(self):
        if self.question:
            temp_string = self.question

            temp_string = temp_string.replace("{1}", "<i><input name=\"question" + str(
                self.id) + "option1\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{2}", "<i><input name=\"question" + str(
                self.id) + "option2\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{3}", "<i><input name=\"question" + str(
                self.id) + "option3\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{4}", "<i><input name=\"question" + str(
                self.id) + "option4\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{5}", "<i><input name=\"question" + str(
                self.id) + "option5\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{6}", "<i><input name=\"question" + str(
                self.id) + "option6\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{7}", "<i><input name=\"question" + str(
                self.id) + "option7\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{8}", "<i><input name=\"question" + str(
                self.id) + "option8\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{9}", "<i><input name=\"question" + str(
                self.id) + "option9\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{10}", "<i><input name=\"question" + str(
                self.id) + "option10\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{11}", "<i><input name=\"question" + str(
                self.id) + "option11\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{12}", "<i><input name=\"question" + str(
                self.id) + "option12\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{13}", "<i><input name=\"question" + str(
                self.id) + "option13\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{14}", "<i><input name=\"question" + str(
                self.id) + "option14\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{15}", "<i><input name=\"question" + str(
                self.id) + "option15\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{16}", "<i><input name=\"question" + str(
                self.id) + "option16\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{17}", "<i><input name=\"question" + str(
                self.id) + "option17\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{18}", "<i><input name=\"question" + str(
                self.id) + "option18\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{19}", "<i><input name=\"question" + str(
                self.id) + "option19\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{20}", "<i><input name=\"question" + str(
                self.id) + "option20\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{21}", "<i><input name=\"question" + str(
                self.id) + "option21\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{22}", "<i><input name=\"question" + str(
                self.id) + "option22\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{23}", "<i><input name=\"question" + str(
                self.id) + "option23\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{24}", "<i><input name=\"question" + str(
                self.id) + "option24\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{25}", "<i><input name=\"question" + str(
                self.id) + "option25\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{26}", "<i><input name=\"question" + str(
                self.id) + "option26\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            temp_string = temp_string.replace("{27}", "<i><input name=\"question" + str(
                self.id) + "option27\" size=\"5\" style=\"border:none;border-bottom: 1px black solid;\" type=\"text\"/></i>")
            self.question_rendered = temp_string

    @api.one
    @api.depends('question_options')
    def calc_options(self):
        self.num_options = self.question_options.search_count([('question_id', '=', self.id)])

    @api.one
    @api.depends('question_options')
    def calc_correct(self):
        self.num_correct = self.question_options.search_count([('question_id', '=', self.id), ('correct', '=', True)])


class EtqQuestionOptionsPrepareLine(models.Model):
    _name = "etq.question.prepare.line.option"
    _rec_name = "option"

    question_id = fields.Many2one('etq.question.prepare.line', string="Question ID")
    option = fields.Char(string="Option")
    correct = fields.Boolean(string="Correct")


class EtqQuestionOptionBlankPrepareLine(models.Model):
    _name = "etq.question.prepare.line.optionblank"

    question_id = fields.Many2one('etq.question.prepare.line', string="Question ID")
    answer = fields.Char(string="Blank Answer")