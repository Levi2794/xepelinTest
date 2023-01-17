# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PaymentConfig(models.Model):
    _name = 'xepelin.payment.config'
    _description = 'Payment Request Configuration'

    name = fields.Char(string='Configuration name')
    value = fields.Char(string='Configuration value')

    @api.constrains('name')
    def _check_unique(self):
        for record in self:
            payment_config = self.search_count([
                ('name', '=', record.name),
            ])
            if payment_config > 1:
                raise ValidationError(
                    'There can only be one configuration with that name.'
                    )
