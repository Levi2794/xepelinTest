# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class PaymentPayment(models.Model):
    _name = 'xepelin.payment.area'
    _description = 'Areas'

    name = fields.Char(string='Name', tracking=True, required=True)
    code = fields.Char(string='Code', tracking=True, required=True)

    @api.model
    def searchAreaByName(self, name_area):
        query = "SELECT * FROM xepelin_payment_area WHERE UPPER(name) = %(name_area)s LIMIT 1"
        self.env.cr.execute(query, { 'name_area': name_area.upper() })
        result = self.env.cr.dictfetchall()
        if len(result) > 0:
            return result[0]
        return None

    @api.constrains('code')
    def _check_unique(self):
        for record in self:
            areas = self.search_count([
                ('code', '=', record.code),
            ])
            if areas > 1:
                raise ValidationError(
                    'There can only be one area with that code.'
                    )
