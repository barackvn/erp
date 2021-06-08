# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _

class AccountMove(models.Model):
	_inherit = "account.invoice"

	debit_origin_id = fields.Many2one('account.move', 'Original Invoice Debited', readonly=True, copy=False)

	@api.multi
	def action_view_debit_notes(self):
		self.ensure_one()
		return {
			'type': 'ir.actions.act_window',
			'name': _('Debit Notes'),
			'res_model': 'account.move',
			'view_mode': 'tree,form',
			'domain': [('debit_origin_id', '=', self.id)],
		}
