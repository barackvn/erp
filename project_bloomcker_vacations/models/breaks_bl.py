# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class breaksBL(models.Model):

    _name = 'breaks.bl'

    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres')
    state = fields.Selection([ ('active', 'Activo'), ('inactive', 'Inactivo')], string='Estado')
    line_ids = fields.One2many('breaks.line.bl', 'breaks_base_id', string='Lineas de Descansos', ondelete='cascade')
    date_init = fields.Date('Fecha de Ingreso', related="employee_id.contract_id.date_start")
    dni = fields.Char('DNI', related="employee_id.identification_id")


class breaksLines(models.Model):

    _name = 'breaks.line.bl'

    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")
    days_total = fields.Integer('Días')
    reason = fields.Char('Motivo')
    period = fields.Many2one('hr.payslip.run', string="Periodo")
    breaks_base_id = fields.Many2one('breaks.bl')
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres', related='breaks_base_id.employee_id', readonly=True)
    amount = fields.Float('Monto')