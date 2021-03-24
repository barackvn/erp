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
    breack_ids = fields.One2many('breack.line.bl', 'vacations_base_id', string='Lineas de Descansos', ondelete='cascade')
    days_devs = fields.Integer('Días Devengados', compute="_get_days")
    days_totals = fields.Integer('Días Totales', compute="_get_days")
    days = fields.Integer('Días por Devengar', compute="_get_days")
    date_init = fields.Date('Fecha de Ingreso', related="employee_id.contract_id.date_start")

    @api.model
    def create(self, vals):
        result = super(VacationsBL,self).create(vals)
        if result:
            result.get_lines()

        return result

    def _get_days(self):
        for i in self:
            for line in i.line_ids:
                i.days_devs += line.days_total

            calculo = fields.Datetime.from_string(str(i.employee_id.contract_id.date_start)) - datetime.now()
            i.days_totals = int(-calculo.days // 360)*30
            i.days = i.days_totals - i.days_devs


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

class BreackLine(models.Model):

    _name = 'breack.line.bl'

    date_start = fields.Date("Fecha de Inicio")
    date_end = fields.Date("Fecha de Fin")
    days_total = fields.Integer('Días')
    dsndes = fields.Char('DSNDes')
    amount = fields.Float('Monto Subsidio')
    type_poised = fields.Selection([ ('inability', 'Incapacidad'), ('other', 'Otros')], string='Tipo de Suspensión')
    period = fields.Many2one('hr.payslip.run', string="Periodo")
    vacations_base_id = fields.Many2one('vacations.bl')
    employee_id = fields.Many2one('hr.employee','Apellidos y Nombres', related='vacations_base_id.employee_id', readonly=True)





