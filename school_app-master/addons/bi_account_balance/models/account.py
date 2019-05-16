# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _

#============================================
#class:AccountAccount
#description:debit, credit, balance in chart of account
#============================================

class AccountAccount(models.Model):
    _inherit = "account.account"
    _description = "Account"
    _order = "code"

    #============================================
    #class:AccountAccount
    #method:_find_account_balance
    #description:debit, credit ,balance in chart of account
    #============================================


    @api.depends('account_move_lines.credit','account_move_lines.debit')
    def _find_account_balance(self):
        
        for account in self:
            values= self.env['account.move.line'].search([('account_id', '=', account.id),('move_id.state', '=', 'posted')])
            total_debit = 0.0
            total_credit = 0.0
            for value in values:
                total_debit = total_debit + value.debit 
                total_credit = total_credit + value.credit       
            account.update({
                    'credit': total_credit,
                    'debit': total_debit,
                    'balance': total_debit - total_credit,
                })
    account_move_lines = fields.One2many('account.move.line', 'account_id', string='Move Lines', copy=False)
    credit = fields.Monetary(string='Credit', readonly=True, compute='_find_account_balance')
    debit = fields.Monetary(string='Debit', readonly=True, compute='_find_account_balance')
    balance = fields.Monetary(string='Balance', readonly=True, compute='_find_account_balance')


    