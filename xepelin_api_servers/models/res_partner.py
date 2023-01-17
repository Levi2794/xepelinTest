# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    xepelin_enable_search_rfc = fields.Boolean(string="Enable Search RFC", compute="_compute_enable_search_rfc")
    xepelin_id = fields.Char(string="Xepelin BO-ID")

    @api.depends('vat','country_id')
    def _compute_enable_search_rfc(self):
        mx_country_id = self.env.ref('base.mx')
        for rec in self:
            enable = False
            if all([not rec.vat, rec.country_id.id == mx_country_id.id]):
                enable = True
            rec.xepelin_enable_search_rfc = enable

    def search_bo_rfc(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Search RFC for: %s" % self.name),
            'res_model': 'search.rfc.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_partner_id': self.id, 'default_search_name': self.name}
        }
