# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class EmployeeExt(models.Model):
    _inherit = 'hr.employee'

    eps_check = fields.Boolean(name="EPS", help="Posee EPS", default=False)
    plan_eps = fields.Char('Plan EPS')
    import_food = fields.Float('Importe Alimentario', default=0)