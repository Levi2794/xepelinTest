# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __manifest__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    server_global_cl_url = fields.Char(
        string="Server Global CL URL",
        config_parameter="xepelin_bank_statement.server_global_cl_url",
    )
    server_global_cl_token = fields.Char(
        string="Server Global CL Token",
        config_parameter="xepelin_bank_statement.server_global_cl_token",
    )
    back_office_cl_url = fields.Char(
        string="Back Office CL URL",
        config_parameter="xepelin_bank_statement.back_office_cl_url",
    )
