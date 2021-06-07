# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import datetime
import logging
logger = logging.getLogger(__name__)


class EmployeeExt(models.Model):

	_inherit = 'hr.employee'

	def _default_entry_bl(self):
		contract_ids = self.env['hr.contract'].search([('employee_id','=',self.id)])
		logger.info(contract_ids)
		if contract_ids:
			contract_ids_sorted_by_date_start = contract_ids.sorted(lambda c: c.date_start)
			return contract_ids_sorted_by_date_start[0].date_start

	def _default_end_bl(self):
		contract_ids = self.env['hr.contract'].search([('employee_id','=',self.id)])
		if contract_ids:
			contract_ids_sorted_by_date_start = contract_ids.sorted(lambda c: c.date_start)
			if contract_ids_sorted_by_date_start[-1].date_end:
				return contract_ids_sorted_by_date_start[-1].date_end

	date_entry = fields.Date('Fecha de Ingreso',default=lambda self: self._default_entry_bl())
	date_end = fields.Date('Fecha de Salida',default=_default_end_bl)