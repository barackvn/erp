# -*- coding: utf-8 -*-
from datetime import datetime, date
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class Attendance_Constrains(models.Model):

    _inherit="hr.attendance"

    entradas_diarias = fields.Integer("Número de jornadas en el día", compute="_compute_asist_diaria", readonly=True)

    @api.multi
    def _compute_asist_diaria(self):
        data_empleado=self.env['hr.attendance'].search([])              
        for entrada in self:
            k=0
            fecha_ent=fields.Datetime.from_string(entrada.check_in).date()
            for data in data_empleado:
                fecha_data=fields.Datetime.from_string(data.check_in).date()
                if data.employee_id == entrada.employee_id and fecha_ent == fecha_data:
                    k+=1
            entrada.entradas_diarias=k

    @api.model
    def create(self,vals):
        res = super(Attendance_Constrains,self).create(vals)
        if res.entradas_diarias > 2:
            raise ValidationError(_("Se han agotado el número de entradas diarias para este empleado"))
        else: 
            return res
