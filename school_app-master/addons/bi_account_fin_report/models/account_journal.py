from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import amount_to_text_en, float_round
import odoo.addons.decimal_precision as dp

class account_financial_report(models.Model):
    _inherit = "account.financial.report"
    _description = "Account Report"

    type = fields.Selection([
        ('sum', 'View'),
        ('accounts', 'Accounts'),
        ('account_type', 'Account Type'),
        ('account_report', 'Report Value'),
        ('account_tag', 'Account Tag'),
        ], 'Type', default='sum')
    account_tag_ids = fields.Many2many('account.account.tag', 'account_account_financial_report_tag', 'report_id', 'account_tag_id', 'Account Tags')


