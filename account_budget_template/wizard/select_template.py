# -*- coding: utf-8 -*-
##############################################################################
#
#    Aurium Technologies,  Morocco
#    Copyright (C) UNamur <http://www.auriumtechnologies.com>
#    Author: Jalal ZAHID (<https://www.auriumtechnologies.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api
from odoo.exceptions import UserError

class BudgetTemplateWizard(models.TransientModel):

    _name = "budget.template.wizard"

    template_id = fields.Many2one(comodel_name='budget.template', string='Budget Template', required=True)
    template_line_ids = fields.One2many(comodel_name='budget.template.wizard.line', inverse_name='template_id', string='Template Lines')
    company_id = fields.Many2one('res.company', 'Company', required=True,default=lambda self: self.env['res.company']._company_default_get('account.budget.post'))
    date_start = fields.Date(string='Date start', required=True)
    date_end = fields.Date(string='Date end', required=True)
    template_selected = fields.Boolean(string="Template selected" , default=False)



    def create_budget(self):

        budget_lines = {}
        wizard = self.browse(self.ids)[0]

        if not self.template_id or not self.date_start or not self.date_end:
            raise UserError(_('Error, fill mandatory fields first !'))

        budget_values = {
            "template": self.template_id.id,
            "name": self.template_id.name,
            "date_from": self.date_start,
            "date_to": self.date_end,
            "company_id": self.company_id.id,
            "state": 'draft',
        }
        budget_obj= self.env["crossovered.budget"]
        # create budget from sselected template
        rec = budget_obj.create(budget_values)

        budget_lines_obj = self.env["crossovered.budget.lines"]

            # create budget lines
        for line in self.template_id.template_lines_ids:
            budget_lines = {
                "crossovered_budget_id": rec.id,
                "general_budget_id": line.budget_position.id,
                "analytic_account_id": line.analytic_account_id.id,
                "planned_amount": line.amount,
                "date_from": rec.date_from,
                "date_to": rec.date_to,
            }
            rec_line = budget_lines_obj.create(budget_lines)


        # display created budget
        domain = [('id', 'in', [rec.id])]
        return {
            'domain': domain,
            'name': 'Budget',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'crossovered.budget',
            'type': 'ir.actions.act_window'
        }




class BudgetTemplateLineWizard(models.TransientModel):
    
    _name = "budget.template.wizard.line"
    
    name = fields.Char(string='Name')
    template_id = fields.Many2one('budget.template.wizard', string='Budget Template')
    budget_position = fields.Many2one('account.budget.post', string='Budget Position')
    amount = fields.Float('Planned amount')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic account')