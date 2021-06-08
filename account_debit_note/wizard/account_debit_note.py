# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)


class AccountDebitNote(models.TransientModel):
	"""
	Add Debit Note wizard: when you want to correct an invoice with a positive amount.
	Opposite of a Credit Note, but different from a regular invoice as you need the link to the original invoice.
	In some cases, also used to cancel Credit Notes
	"""
	_name = 'account.debit.note'
	_description = 'Add Debit Note wizard'

	move_ids = fields.Many2many('account.move', 'account_move_debit_move', 'debit_id', 'move_id',
								domain=[('state', '=', 'posted')])
	date = fields.Date(string='Fecha Nota', default=fields.Date.context_today, required=True)
	reason = fields.Char(string='Razon',required=True)
	debit_invoice_type = fields.Many2one('einvoice.catalog.10',string='Tipo nota',required=True)
	serie_id = fields.Many2one('it.invoice.serie', string='Serie',
								 help='If empty, uses the journal of the journal entry to be debited.',domain=[('type_document_id.code','=','08')],required=True)
	copy_lines = fields.Boolean("Copiar lineas",
								help="In case you need to do corrections for every line, it can be in handy to copy them.  "
									 "We won't copy them for debit notes from credit notes. ",default=True)

	@api.model
	def default_get(self, fields):
		res = super(AccountDebitNote, self).default_get(fields)
		move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.env['account.move']
		if any(move.state != "posted" for move in move_ids):
			raise UserError(_('You can only debit posted moves.'))
		res['move_ids'] = [(6, 0, move_ids.ids)]
		return res

	@api.model
	def _prepare_default_values(self, move):
		_logger.info('_prepare_default_values')
		if move.type in ('in_refund', 'out_refund'):
			type = 'in_invoice' if move.type == 'in_refund' else 'out_invoice'
		else:
			type = move.type
		default_values = {
				'ref': '%s, %s' % (move.name, self.reason) if self.reason else move.name,
				'date': self.date or move.date,
				'invoice_date': move.is_invoice(include_receipts=True) and (self.date or move.date) or False,
				'serie_id': self.serie_id and self.serie_id.id or move.serie_id.id,
				'invoice_payment_term_id': None,
				'debit_origin_id': move.id,
				'type': type,
			}
		if not self.copy_lines or move.type in [('in_refund', 'out_refund')]:
			default_values['line_ids'] = [(5, 0, 0)]
		_logger.info(default_values)
		return default_values

	@api.multi
	def create_debit(self):
		inv_obj = self.env['account.invoice']
		inv_tax_obj = self.env['account.invoice.tax']
		inv_line_obj = self.env['account.invoice.line']
		for form in self:
			account_invoice_id = int(self.env.context['active_id'])
			inv = self.env['account.invoice'].sudo().browse(account_invoice_id)
			invoice_lines = inv_line_obj.browse(inv['invoice_line_ids'])
			tax_lines = inv_tax_obj.browse(inv['tax_line_ids'])
			invoice_lines_ids = []
			tax_line_ids = []

			next_number = form.serie_id.sequence_id.number_next_actual
			prefix = form.serie_id.sequence_id.prefix
			padding = form.serie_id.sequence_id.padding
			reference = prefix + "0"*(padding - len(str(next_number))) + str(next_number)

			for invoice_line in inv['invoice_line_ids']:
				invoice_line_dict = {
					'quantity':invoice_line.quantity,
					'name': invoice_line.name,
					'price_unit': invoice_line.price_unit,
					'account_id': invoice_line.account_id.id,
					'product_id': invoice_line.product_id.id if invoice_line.product_id else False,
					'invoice_line_tax_ids': [(6, 0, [invoice_line.invoice_line_tax_ids[0].id])],
				}
				invoice_lines_ids.append((0,0,invoice_line_dict))

			if not form.copy_lines:
				_logger.info('copy_lines')
				invoice_lines_ids = [(5, 0, 0)]

			_logger.info('invoice_lines_ids')
			_logger.info(invoice_lines_ids)
			for tax_line in tax_lines:
				  tax_line_ids.append(tax_line.id)



			_logger.info(tax_line_ids)
			it_type_document = self.env['einvoice.catalog.01'].search([('code','=','08')],limit=1)

			related_documents = []
			val = {}
			val['tipo_doc'] = inv.it_type_document.id   #einvoice.catalog.01
			val['comprobante'] = inv.reference
			val['fecha'] = inv.date_invoice
			val['igv'] = inv.amount_tax
			val['base_imponible'] = inv.amount_untaxed
			val['perception'] = inv.amount_total
			related_documents = [(0, 0, val)]
			# [(6, 0, self.account_ids.ids)]
			# values['account_ids'] = related_documents

			invoice = {
				'name': form.reason,
				'type': inv.type,
				'date_invoice': form.date,
				'state': 'draft',
				'reference':reference,
				'number': False,
				'origin': inv.origin,
				'account_ids':related_documents,
				'it_type_document': it_type_document.id,
				'serie_id': form.serie_id.id,
				'journal_id': inv.journal_id.id,
				'partner_id': inv.partner_id.id,
				'fiscal_position_id': inv.fiscal_position_id.id,
				'invoice_line_ids': invoice_lines_ids,
				'debit_invoice_type': form.debit_invoice_type.id
			}
			_logger.info(invoice)
			inv_refund = inv_obj.create(invoice)

			action = {
				'name': _('Debit Notes'),
				'type': 'ir.actions.act_window',
				'res_model': 'account.invoice',
				}
			_logger.info(inv_refund)
			_logger.info(inv_refund.id)
			if len(inv_refund) == 1:
				_logger.info('1')
				action.update({
					'view_mode': 'form',
					'res_id': inv_refund.id,
				})
			else:
				action.update({
					'view_mode': 'tree,form',
					'domain': [('id', 'in', inv_refund.ids)],
				})
			return action
