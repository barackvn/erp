# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime

class VacationsBL(models.Model):

    _name = 'vacations.bl'

    code = fields.Char('Codigo')
    dni = fields.Char('DNI', compute="_get_dni")
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres')
    state = fields.Selection([ ('active', 'Activo'), ('inactive', 'Inactivo')], string='Estado')
    line_ids = fields.One2many('vacations.line.bl', 'vacations_base_id', string='Lineas de Vacaciones', ondelete='cascade')
    days_totals = fields.Integer('Días Totales', compute="_get_days")

    @api.model
    def create(self, vals):
        result = super(VacationsBL,self).create(vals)
        if result:
            result.get_lines()

        return result

    def _get_days(self):
        for i in self:
            for line in i.line_ids:
                i.days_totals += line.days_total

    def _get_dni(self):
        for i in self:
            i.dni = i.employee_id.identification_id

    def _get_employees(self):
        employees = self.env['hr.employee'].search([])
        for employee in employees:
            vals = {
                'code':'0',
                'employee_id':employee.id,
                'state':'inactive',
            }
            line = self.env['vacations.bl'].create(vals)


    def get_lines(self):

        if self.line_ids:
            self.line_ids.unlink()

        devengues = self.env['hr.devengue'].search([('employee_id', '=', self.employee_id.id)])
        for devengue in devengues:
            vals = {
                'period':devengue.periodo_devengue.id,
                'employee_id':devengue.employee_id.id,
                'days_total':devengue.dias,
                'date_start':devengue.date_start,
                'date_end':devengue.date_end,
                'vacations_base_id':self.id,
            }
            line = self.env['vacations.line.bl'].create(vals)

class VacationsLine(models.Model):

    _name = 'vacations.line.bl'

    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")
    days_total = fields.Integer('Días')
    period = fields.Many2one('hr.payslip.run', string="Periodo")
    vacations_base_id = fields.Many2one('vacations.bl')
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres', related='vacations_base_id.employee_id', readonly=True)





