# -*- coding: utf-8 -*-

from odoo import _, api, fields, models

from odoo.addons.base.models.res_partner import _tz_get


class ResCompany(models.Model):
    _inherit = "res.company"

    tz = fields.Selection(
        _tz_get, string="Timezone", default=lambda self: self._context.get("tz")
    )
