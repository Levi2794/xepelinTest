# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                  #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    server_global_mx_url = fields.Char(
        string="Server Global MX URL",
        config_parameter="xepelin_movement.server_global_mx_url",
    )
    server_global_mx_token = fields.Char(
        string="Server Global MX Token",
        config_parameter="xepelin_movement.server_global_mx_token",
    )
    back_office_mx_url = fields.Char(
        string="Back Office MX URL",
        config_parameter="xepelin_movement.back_office_mx_url",
    )
