from odoo import api, fields, models, tools, _

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    dias_calendarios = fields.Integer(string="Dias Calendarios", default=6)
