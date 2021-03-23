# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging


class DevengueExt(models.Model):
    _inherit = 'hr.devengue'

    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")