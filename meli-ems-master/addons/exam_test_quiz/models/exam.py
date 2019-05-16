import time
from datetime import date, datetime, timedelta,time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError,Warning as UserError
import babel

from odoo import api, fields, models,_
class ExamExam(models.Model):
    _inherit = 'exam.exam'
    _description = 'Exam Information'
    online_exam_ids = fields.Many2many('etq.exam', string='Online Exams')

    @api.multi
    def action_view_exam(self):
        action = self.env.ref('exam_test_quiz.etq_exam_action')
        result = action.read()[0]
        result['context'] = {'default_exam_id': self.id,'default_name':self.name}
        if len(self.online_exam_ids) > 1:
            result['domain'] = "[('id', 'in', " + str(self.online_exam_ids.ids) + ")]"
        elif len(self.online_exam_ids) == 1:
            res = self.env.ref('exam_test_quiz.etq_exam_form_view', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.online_exam_ids.id
        elif len(self.online_exam_ids) == 0:
            raise UserError(
                _('Please Generate Online Exam'))

        return result

    @api.multi
    def generate_online_exam(self):
        time_table_obj = self.mapped('exam_schedule_ids.timetable_id.exam_timetable_line_ids')
        exam_ids =[]
        vals =[]
        exam_obj = self.env['etq.exam']
        question_obj = self.env['etq.question']
        for line in time_table_obj:
            if line.id not in exam_obj.search([]).mapped('exam_timetable_line_id').ids:
                res = {
                    'name': self.name + '-' + line.subject_id.name,
                    'exam_id': self.id,
                    'exam_timetable_line_id': line.id,
                }
                time = self._prepare_datetime(line)
                if time:
                    res['start_time'] = time['start_datetime']
                    res['end_time'] = time['end_datetime']

                if line.question_id:
                    vals = self._prepare_question(line.question_id)
                    res['questions'] =  vals

                exam_id = exam_obj.create(res)
                exam_id._onchange_time()

                exam_ids.append(exam_id.id)

        if exam_ids:
            self.update({'online_exam_ids': [(6, 0, exam_ids)]})
            self.action_view_exam()

    @api.model
    def _prepare_datetime(self, line):
        res = {}
        if line.start_time and line.exm_date:
            start_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(line.start_time * 60, 60))
            start_date = datetime.strptime(line.exm_date, "%Y-%m-%d").date()
            res['start_datetime'] = datetime.combine(start_date,
                             time(int(start_time[0:2]),int(start_time[3:5]))).strftime("%Y-%m-%d %H:%M:%S")

        if line.end_time and line.exm_date:
            end_time = '{0:02.0f}:{1:02.0f}'.format(*divmod(line.end_time * 60, 60))
            start_date = datetime.strptime(line.exm_date, "%Y-%m-%d").date()
            res['end_datetime'] = datetime.combine(start_date,
                                                 time(int(end_time[0:2]),int(end_time[3:5]))).strftime("%Y-%m-%d %H:%M:%S")
        return res


    @api.model
    def _prepare_question(self,questions):
        res =[]
        if not questions.questions:
            return res

        for qut in questions.questions:
            val = {
                'image': qut.image,
                # 'exam_id':exam_id,
                'question': qut.question,
                'question_rendered': qut.question_rendered,
                'question_type': qut.question_type,
                'question_options': qut.question_options,
                'question_options_blank': qut.question_options_blank,
                'num_options': qut.num_options,
                'num_correct': qut.num_correct
            }


            res.append((0, 0, val))
        return res


class ExtendedTimeTableLine(models.Model):
    _inherit = 'time.table.line'

    question_id = fields.Many2one(
        'etq.question.prepare',
        string='Question',
    )

    standard_id = fields.Many2one('school.standard', 'Class')
