# -*- coding: utf-8 -*-

from odoo import api, models

class PaymentBank(models.Model):
    _name = 'xepelin.payment.bank'
    _inherit = ['res.bank']

    @api.model
    def searchByName(self, name_bank):
        query = "SELECT * FROM res_bank WHERE UPPER(name) = %(name_bank)s LIMIT 1"
        self.env.cr.execute(query, { 'name_bank': name_bank.upper() })
        result = self.env.cr.dictfetchall()
        if len(result) > 0:
            return result[0]
        return None