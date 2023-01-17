# -*- coding: utf-8 -*-

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError


class SearchRFC(models.TransientModel):
    _name = "search.rfc.wizard"
    _description = "Search RFC"

    partner_id = fields.Many2one("res.partner", string="Partner")
    search_name = fields.Char(string="Search name")

    def action_search(self):
        server_global_obj = self.env["server.global"]
        server_global_id = server_global_obj.search(
                [('company_id', '=', self.env.company.id)], limit=1)

        if not server_global_id:
            raise ValidationError(_('No connection to global server found.'))

        partner_vat, partner_name = server_global_id.search_partner_vat(self.search_name)
        if not partner_vat:
            raise ValidationError(_('no contact found in SG with name: %s' % self.search_name))
        else:
            self.partner_id.with_context(no_vat_validation=True).write({
                'name': partner_name,
                'vat':partner_vat
                })

        return True
