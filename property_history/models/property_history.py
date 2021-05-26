# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import time

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, Warning
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime
import logging
_logger = logging.getLogger(__name__)


class PropertyHistory(models.Model):
	_name = 'property.history'

	activo = fields.Many2one('account.asset.asset',string="Activo")
	propietario = fields.Many2one('res.partner',string="Propietario")
	fecha = fields.Date('Fecha')
	inquilino = fields.Char(string="Inquilino")
	moneda = fields.Many2one('res.currency',string="Moneda")
	factura = fields.Char(string="Factura")
	glosa1 = fields.Char(string="Glosa1")
	glosa2 = fields.Char(string="Glosa2")
	gfa_meter = fields.Float(string="Metro cuadrado")
	costoporm2 = fields.Float(string="Costo por metro cuadrado")
	valvta = fields.Float(string="Valor de venta")
	inavta = fields.Float(string="Inafecto")
	igvvta = fields.Float(string="IGV")
	detrac = fields.Float(string="Detraccion")
	totvta = fields.Float(string="Total venta")

	@api.model
	def get_the_top_products(self,datetype,date_to=None,date_from=None):
		if date_to==None:
			date_to = datetime.today().strftime('%Y-%m-%d')
		if date_from==None:
			date_from = (datetime.strptime(fields.Date.today(), '%Y-%m-%d') + relativedelta(years=-10)).strftime('%Y-%m-%d')
		if not date_from:
			date_from = (datetime.strptime(fields.Date.today(), '%Y-%m-%d') + relativedelta(years=-10)).strftime('%Y-%m-%d')

		total_amount = []
		month_year_name = []
		if datetype == 'month':
			query_vista = """
							select
							to_char(fecha, 'YYYY') as year,
							to_char(fecha, 'MM') as month,
							sum(valvta) as monto
							from property_history
							where (fecha between '%s' AND '%s')
							group by to_char(fecha, 'YYYY'), to_char(fecha, 'MM')
							order by to_char(fecha, 'YYYY') asc, to_char(fecha, 'MM') asc
							""" % (date_from,date_to)
			# AND (date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))
			self.env.cr.execute(query_vista)
			data = self.env.cr.dictfetchall()
			mapped_data = list([(d['monto'], d['year'] + '-' + d['month']) for d in data])
		if datetype == 'year':
			query_vista = """
							select
							to_char(fecha, 'YYYY') as year,
							sum(valvta) as monto
							from property_history
							where (fecha between '%s' AND '%s')
							group by to_char(fecha, 'YYYY')
							order by to_char(fecha, 'YYYY') asc
							""" % (date_from,date_to)
			# AND (date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))
			self.env.cr.execute(query_vista)
			data = self.env.cr.dictfetchall()

			mapped_data = list([(d['monto'], d['year']) for d in data])

		for m in mapped_data:
			total_amount.append(m[0])
			month_year_name.append(m[1])
		final = [total_amount,month_year_name]

		return final


	# @api.model
	# def get_the_available_meters(self,datetype,date_to=None,date_from=None):
	# 	_logger.info('get_the_available_meters2')
	# 	if date_to==None:
	# 		date_to = datetime.today().strftime('%Y-%m-%d')
	# 	if date_from==None:
	# 		date_from = (datetime.strptime(fields.Date.today(), '%Y-%m-%d') + relativedelta(years=-10)).strftime('%Y-%m-%d')
	# 	if not date_from:
	# 		date_from = (datetime.strptime(fields.Date.today(), '%Y-%m-%d') + relativedelta(years=-10)).strftime('%Y-%m-%d')
	#
	# 	assets = self.env['account.asset.asset'].search([])
	# 	total_amount = []
	# 	month_year_name = []
	# 	total_on_lease = []
	# 	if datetype == 'month':
	# 		query_vista = """
	# 						select
	# 						to_char(ph.fecha, 'YYYY') as year,
	# 						to_char(ph.fecha, 'MM') as month,
	# 						sum(ph.gfa_meter) as total_meter,
	# 						ph.activo as name
	# 						from property_history as ph
	# 						join account_asset_asset as aaa
	# 						on aaa.id = ph.activo
	# 						where (ph.fecha between '%s' AND '%s')
	# 						group by to_char(ph.fecha, 'YYYY'), to_char(ph.fecha, 'MM'),
	# 						order by to_char(ph.fecha, 'YYYY') asc, to_char(ph.fecha, 'MM') asc
	# 						""" %  (date_from,date_to)
	# 		# AND (date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))
	# 		self.env.cr.execute(query_vista)
	# 		data = self.env.cr.dictfetchall()
	# 		_logger.info(data)
	# 		mapped_data = list([(d['total_meter'], d['year'] + '-' + d['month'], d['total_on_lease']) for d in data])
	# 	if datetype == 'year':
	# 		query_vista = """
	# 						select
	# 						to_char(fecha, 'YYYY') as year,
	# 						sum(gfa_meter) as total_meter,
	# 						sum(case when state = 'normal' then (gfa_meter) else (0) end) as total_on_lease
	# 						from account_asset_asset
	# 						where (fecha between '%s' AND '%s')
	# 						group by to_char(fecha, 'YYYY')
	# 						order by to_char(fecha, 'YYYY') asc
	# 						""" %  (date_from,date_to)
	# 		# AND (date between to_date(%s,'yyyy-mm-dd') AND to_date(%s,'yyyy-mm-dd'))
	# 		self.env.cr.execute(query_vista)
	# 		data = self.env.cr.dictfetchall()
	#
	# 		mapped_data = list([(d['total_meter'], d['year'], d['total_on_lease']) for d in data])
	#
	# 	for m in mapped_data:
	# 		total_amount.append(m[0])
	# 		month_year_name.append(m[1])
	# 		total_on_lease.append(m[2])
	# 	final = [total_amount,month_year_name,total_on_lease]
	#
	# 	return final
