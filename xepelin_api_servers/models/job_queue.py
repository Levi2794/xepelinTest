# -*- coding: utf-8 -*-

import logging
import requests
from odoo import fields, models
from odoo.tools.safe_eval import safe_eval
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)



class JobQueue(models.Model):
    _name = 'xepelin.job.queue'
    _description = 'Xepelin Job Queue'

    name = fields.Char(string="Job Name", required=True)
    code = fields.Text(string="Python code", required=True)
    status = fields.Selection(selection=[
        ('draft','Draft'),
        ('prepared','Prepared'),
        ('running','Running'),
        ('finished','Finished'),
        ('failure','Failure'),
        ('canceled','Canceled')],
        default="draft",
        string="Status")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True)

    def action_prepared(self):
        self.status = "prepared"

    def action_cancel(self):
        self.status = "canceled"

    def set_job_search_partners(self):
        companies = self.env['res.company'].search([])
        for company in companies:
            server_global_obj = self.env["server.global"]
            server_global_id = server_global_obj.search(
                [('company_id', '=', company.id)], limit=1)

            if server_global_id:
                size = 200
                host, token = server_global_id._get_sever_params()
                URL = "%s/api/backoffice/business" % (host)
                country_code = server_global_id.company_id.country_id.code
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": "Bearer %s" % token,
                }
                params = {
                    "page": 1,
                    "size": size,
                    "country": country_code,
                }
                r = requests.get(URL, headers=headers, params=params)
                if r.ok:
                    
                    response_json = r.json()
                    pagination = response_json.get("pagination", {})
                    if pagination:
                        for i in range(pagination['totalPages']):
                            self.create({
                                "name": "GET PARTNERS FROM BO %s/%s" %(i+1, pagination['totalPages']),
                                "status": "prepared",
                                "company_id": company.id,
                                "code": """
server_global_obj = self.env["server.global"]
server_global_id = server_global_obj.search(
    [('company_id', '=', %s)], limit=1)
server_global_id.search_all_partners(size=%s, page=%s)
                                """ %(company.id, size, i+1)
                                })
                else:
                    _logger.exception('A problem occurred while consulting contacts in BO')
                    return False
            else:
                _logger.warning('There is no global server configuration available for the company: %s' % company.name)
                return False

    def run_job(self):
        job_id = self.search([('status','=','prepared')],limit=1)
        if job_id and job_id.code:
            try:
                job_id.status = "running"
                cxt = {'self': self}
                safe_eval(job_id.code, cxt, mode="exec", nocopy=True)
                job_id.status = "finished"
            except:
                job_id.status = "failure"
