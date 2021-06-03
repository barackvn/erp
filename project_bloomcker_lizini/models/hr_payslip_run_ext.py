# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from datetime import date, datetime
from odoo.exceptions import ValidationError, UserError
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import magenta, red, black, blue, gray, Color, HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.platypus import Paragraph, Table, PageBreak
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import simpleSplit
from cgi import escape
import base64
import io
from xlsxwriter.workbook import Workbook
import sys
reload(sys)
sys.setdefaultencoding('iso-8859-1')
import os
import copy
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, inch, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import StringIO
import time
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

import calendar
from datetime import date, datetime
from openerp.osv import osv
from math import modf
from decimal import *

class HrPayslipRun(models.Model):

	_inherit = 'hr.payslip.run'

	#FIXME: deprecado
	@api.depends('date_start', 'date_end')
	def _calcula_dias_calendarios(self):
		self.dias_calendarios = calendar.monthrange(
			2022, 5)[0]

	def genera_planilla_afp_net(self):
		import io
		from xlsxwriter.workbook import Workbook
		output = io.BytesIO()
		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		workbook = Workbook(direccion + 'planilla_afp_net.xls')

		for record in self:

			planilla_ajustes = record.env['planilla.ajustes'].search([], limit=1)

			for payslip_run in record.browse(record.ids):
				query_vista = """  DROP VIEW IF EXISTS planilla_afp_net_xlsx;
					create or replace view planilla_afp_net_xlsx as (

					select row_number() OVER () AS id,* from
					(

						select  hc.cuspp,ptd.codigo_afp as tipo_doc,he.identification_id,he.a_paterno,he.a_materno,he.nombres,
						case
							when (hc.date_end isnull or hc.date_end<='%s' or hc.date_end>='%s') then 'S'
						else
							'N' end as relacion_laboral,
						case
							when (hc.date_start between '%s' and '%s') then 'S'
						else
							'N' end as inicio_relacion_laboral,
						case
							when (hc.date_end between '%s' and '%s') then 'S'
						else
							'N' end as cese_relacion_laboral,
							hc.excepcion_aportador,
						(select total from hr_payslip_line
								where slip_id = p.id and  code = '%s' ) as remuneracion_asegurable,
						(SELECT ''::TEXT as aporte_fin_provisional),
						(SELECT ''::TEXT as aporte_sin_fin_provisional),
						(SELECT ''::TEXT as aporte_voluntario_empleador),
						case
							when (hc.regimen_laboral isnull) then 'N'
						else
							hc.regimen_laboral end as regimen_laboral
						from hr_payslip_run hpr
						inner join hr_payslip p
						on p.payslip_run_id = hpr.id
						inner join hr_contract hc
						on hc.id = p.contract_id
						inner join hr_employee he
						on he.id = hc.employee_id
						left join planilla_tipo_documento ptd
						on ptd.id = he.tablas_tipo_documento_id
						inner join planilla_afiliacion pa on pa.id = hc.afiliacion_id
						where pa.entidad like '%s' and hpr.id= %d
							) T
					)""" % (payslip_run.date_end, payslip_run.date_end,
							payslip_run.date_start, payslip_run.date_end,
							payslip_run.date_start, payslip_run.date_end,
							planilla_ajustes.cod_remuneracion_asegurable.code if planilla_ajustes else '',
							'AFP%',
							payslip_run.id)
				record.env.cr.execute(query_vista)

				worksheet = workbook.add_worksheet(
					str(payslip_run.id)+'-'+payslip_run.date_start+'-'+payslip_run.date_end)
				worksheet.set_landscape()  # Horizontal
				worksheet.set_paper(9)  # A-4
				worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
				worksheet.fit_to_pages(1, 0)  # Ajustar por Columna

				bold = workbook.add_format({'bold': True})
				normal = workbook.add_format()
				boldbord = workbook.add_format({'bold': True})
				boldbord.set_border(style=2)
				boldbord.set_align('center')
				boldbord.set_align('vcenter')
				boldbord.set_text_wrap()
				boldbord.set_font_size(9)
				boldbord.set_bg_color('#DCE6F1')
				numbertres = workbook.add_format({'num_format': '0.000'})
				numberdos = workbook.add_format({'num_format': '0.00'})
				bord = workbook.add_format()
				bord.set_border(style=1)
				bord.set_text_wrap()
				# numberdos.set_border(style=1)
				numbertres.set_border(style=1)

				title = workbook.add_format({'bold': True})
				title.set_align('center')
				title.set_align('vcenter')
				title.set_text_wrap()
				title.set_font_size(20)
				# worksheet.set_row(0, 30)

				x = 0

				import sys
				reload(sys)
				sys.setdefaultencoding('iso-8859-1')

				filtro = []
				for line in record.env['planilla.afp.net.xlsx'].search(filtro):
					worksheet.write(x, 0, line.id if line.id else '')
					worksheet.write(x, 1, line.cuspp if line.cuspp else '')
					worksheet.write(x, 2, line.tipo_doc if line.tipo_doc else '')
					worksheet.write(x, 3, line.identification_id if line.identification_id else '')
					worksheet.write(x, 4, line.a_paterno)
					worksheet.write(x, 5, line.a_materno)
					worksheet.write(x, 6, line.nombres)
					worksheet.write(x, 7, line.relacion_laboral if line.relacion_laboral else '')
					worksheet.write(x, 8, line.inicio_relacion_laboral if line.inicio_relacion_laboral else '')
					worksheet.write(x, 9, line.cese_relacion_laboral if line.cese_relacion_laboral else '')
					worksheet.write(x, 10, line.excepcion_aportador if line.excepcion_aportador else '')
					worksheet.write(x, 11, line.remuneracion_asegurable, numberdos)
					worksheet.write(x, 12, line.aporte_fin_provisional, numberdos)
					worksheet.write(x, 13, line.aporte_sin_fin_provisional, numberdos)
					worksheet.write(x, 14, line.aporte_voluntario_empleador, numberdos)
					worksheet.write(x, 15, line.regimen_laboral if line.regimen_laboral else '')

					x = x + 1

					tam_col = [2, 15, 2, 10, 10, 10, 35, 1, 1, 1, 1,
						   	8, 5, 5, 1, 1]

					worksheet.set_column('A:A', tam_col[0])
					worksheet.set_column('B:B', tam_col[1])
					worksheet.set_column('C:C', tam_col[2])
					worksheet.set_column('D:D', tam_col[3])
					worksheet.set_column('E:E', tam_col[4])
					worksheet.set_column('F:F', tam_col[5])
					worksheet.set_column('G:G', tam_col[6])
					worksheet.set_column('H:H', tam_col[7])
					worksheet.set_column('I:I', tam_col[8])
					worksheet.set_column('J:J', tam_col[9])
					worksheet.set_column('K:K', tam_col[10])
					worksheet.set_column('L:L', tam_col[11])
					worksheet.set_column('M:M', tam_col[12])
					worksheet.set_column('O:O', tam_col[13])
					worksheet.set_column('P:P', tam_col[14])

		workbook.close()

		f = open(direccion+'planilla_afp_net.xls', 'rb')

		vals = {
			'output_name': 'planilla_afp_net.xls',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	def exportar_plame(self):

		output = io.BytesIO()
		# workbook = Workbook('planilla_plame.xls')

		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		docname = ruta+'0601%s%s%s.rem' % (
			self[-1].date_end[:4], self[-1].date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')

		f = open(docname, "w+")
		for record in self:
			for payslip_run in record.browse(record.ids):
				employees = []
				for payslip in payslip_run.slip_ids:
					if payslip.employee_id.id not in employees:
						query_vista = """
							select
							min(ptd.codigo_sunat) as tipo_doc,
							e.identification_id as dni,
							sr.cod_sunat as sunat,
							sum(hpl.total) as monto_devengado,
							sum(hpl.total) as monto_pagado
							from hr_payslip_run hpr
							inner join hr_payslip hp on hpr.id= hp.payslip_run_id
							inner join hr_payslip_line hpl on hp.id=hpl.slip_id
							inner join hr_salary_rule as sr on sr.code = hpl.code
							inner join hr_employee e on e.id = hpl.employee_id
							inner join hr_salary_rule_category hsrc on hsrc.id = hpl.category_id
							left join planilla_tipo_documento ptd on ptd.id = e.tablas_tipo_documento_id
							where  hpr.id = %d
							and e.id = %d
							and sr.cod_sunat != ''
							and hpl.appears_on_payslip = 't'
							group by sr.cod_sunat,e.identification_id
							order by sr.cod_sunat""" % (payslip_run.id,payslip.employee_id.id)
						record.env.cr.execute(query_vista)
						data = record.env.cr.dictfetchall()
						for line in data:
							f.write("%s|%s|%s|%s|%s|\r\n"%(
									line['tipo_doc'],
									line['dni'],
									line['sunat'],
									line['monto_devengado'],
									line['monto_pagado']
									))
					employees.append(payslip.employee_id.id)
		f.close()
		f = open(docname,'rb')
		vals = {
			'output_name': '0601%s%s%s.rem' % (
			self[-1].date_end[:4], self[-1].date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else ''),
			'output_file': base64.encodestring(''.join(f.readlines())),
		}
		sfs_id = self.env['planilla.export.file'].create(vals)

		#os.remove(docname)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def exportar_plame_horas(self):

		output = io.BytesIO()

		# workbook = Workbook('planilla_plame.xls')
		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		docname = ruta+'0601%s%s%s.jor' % (self[-1].date_end[:4], self[-1].date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')

		f = open(docname, "w+")
		for record in self:
			for payslip_run in record.browse(record.ids):
				employees = []
				for payslip in payslip_run.slip_ids:
					if payslip.employee_id.id not in employees:
						sql = """
							select
							coalesce(ptd.codigo_sunat,'') as code,
							he.identification_id as dni,
							sum(case when hpwd.code = '%s' then hpwd.number_of_days else 0 end) as dlab,
							sum(case when hpwd.code = '%s' then hpwd.number_of_days else 0 end) as fal,
							sum(case when hpwd.code = 'H25' then hpwd.number_of_hours else 0 end) as h25,
							sum(case when hpwd.code = 'H35' then hpwd.number_of_hours else 0 end) as h35,
							sum(case when hpwd.code = 'H100' then hpwd.number_of_hours else 0 end) as h100
							from hr_payslip hp
							inner join hr_employee he on he.id = hp.employee_id
							inner join planilla_tipo_documento ptd on ptd.id = he.tablas_tipo_documento_id
							inner join hr_payslip_worked_days hpwd on hpwd.payslip_id = hp.id
							where hp.payslip_run_id = %d
							and hp.employee_id = %d
							and hpwd.code in ('%s','%s','HE25','HE35','HE100')
							group by ptd.codigo_sunat,he.identification_id
						"""%(planilla_ajustes.cod_dias_laborados.codigo,
							planilla_ajustes.cod_dias_no_laborados.codigo,
							payslip_run.id,
							payslip.employee_id.id,
							planilla_ajustes.cod_dias_laborados.codigo,
							planilla_ajustes.cod_dias_no_laborados.codigo
							)
						record.env.cr.execute(sql)
						data = record.env.cr.dictfetchone()
						dias_laborados=int(data['dlab'])-int(payslip.feriados) if not payslip.contract_id.hourly_worker else 0
						if payslip.employee_id.calendar_id.id:
							total = payslip.employee_id.calendar_id.average_hours if payslip.employee_id.calendar_id.average_hours > 0 else 8
						else:
							total = 8
						# formula para los dias laborados segun sunat
						if not payslip.contract_id.hourly_worker:
							total_horas_jornada_ordinaria = (dias_laborados-int(data['fal']))*int(total)
						else:
							total_horas_jornada_ordinaria = sum(payslip.worked_days_line_ids.filtered(lambda l:l.code == planilla_ajustes.cod_dias_laborados.codigo).mapped('number_of_hours'))
						horas_extra = int(data['h25']) + int(data['h35']) + int(data['h100'])
						f.write(str(data['code'])+'|'+str(data['dni'])+'|'+str(total_horas_jornada_ordinaria)+'|0|'+str(horas_extra)+"|0|\r\n")
						employees.append(payslip.employee_id.id)
		f.close()
		f = open(docname,'rb')
		vals = {
			'output_name': '0601%s%s%s.jor' % (
			self[-1].date_end[:4], self[-1].date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else ''),
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def exportar_plame_subsidios(self):

		output = io.BytesIO()

		# workbook = Workbook('planilla_plame.xls')
		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		file_name = '0601%s%s%s.snl' % (self[-1].date_end[:4], self[-1].date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')
		docname = ruta+file_name

		f = open(docname, "w+")
		for record in self:

			for payslip_run in record.browse(record.ids):
				employees = []
				for payslip in payslip_run.slip_ids:
					if payslip.employee_id.id not in employees:
						sql = """
						select
						max(he.identification_id) as dni,
						max(ptd.codigo_sunat) as sunat_code,
						pts.codigo as code,
						sum(hls.nro_dias) as dias
						from hr_payslip hp
						inner join hr_employee he on he.id = hp.employee_id
						inner join hr_contract hc on hc.id = hp.contract_id
						inner join planilla_tipo_documento ptd on ptd.id = he.tablas_tipo_documento_id
						inner join hr_labor_suspension hls on hls.suspension_id = hc.id
						inner join planilla_tipo_suspension pts on pts.id = hls.tipo_suspension_id
						where hp.payslip_run_id = %d
						and hp.employee_id = %d
						and hls.periodos = %d
						group by hp.employee_id,pts.codigo
						"""%(payslip_run.id,payslip.employee_id.id,payslip_run.id)
						record.env.cr.execute(sql)
						data = record.env.cr.dictfetchall()
						for i in data:
							f.write(str(i['sunat_code'])+'|'+str(i['dni'])+'|'+str(i['code'])+'|'+str(i['dias'])+"|\r\n")
						employees.append(payslip.employee_id.id)

		f.close()
		f = open(docname,'rb')
		vals = {
			'output_name': file_name,
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def exportar_plame_tasas(self):

		output = io.BytesIO()

		# workbook = Workbook('planilla_plame.xls')
		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		try:
			ruta = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
		file_name = '0601%s%s%s.tas' % (self[-1].date_end[:4], self[-1].date_end[5:7], planilla_ajustes.ruc if planilla_ajustes else '')
		docname = ruta+file_name

		f = open(docname, "w+")
		for record in self:

			for payslip_run in record.browse(record.ids):
				employees = []
				for payslip in payslip_run.slip_ids:
					if payslip.employee_id.id not in employees:
						payslips = record.env['hr.payslip'].search([('employee_id','=',payslip.employee_id.id)])
						if len(payslips) > 1:
							last_contract = max(payslips.mapped('contract_id'),key=lambda c:c['date_start'])
							sctr = last_contract.sctr if last_contract.sctr else False
						else:
							sctr = payslip.contract_id.sctr if payslip.contract_id.sctr else False
						if sctr:
							cod_sunat = payslip.employee_id.tablas_tipo_documento_id.codigo_sunat if payslip.employee_id.tablas_tipo_documento_id else ''
							dni = payslip.employee_id.identification_id
							f.write(str(cod_sunat)+'|'+str(dni)+'|'+str(sctr.code)+'|'+str(sctr.porcentaje)+"|\r\n")
							employees.append(payslip.employee_id.id)

		f.close()
		f = open(docname,'rb')
		vals = {
			'output_name': file_name,
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	@api.multi
	def exportar_planilla_tabular_xlsx(self):

		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')

		workbook = Workbook(direccion+'planilla_tabular.xls')

		for record in self:

			record.env['planilla.planilla.tabular.wizard'].reconstruye_tabla(record.date_start,record.date_end)

			worksheet = workbook.add_worksheet(
				str(record.id)+'-'+record.date_start+'-'+record.date_end)			#Cambiar este nombre
			worksheet.set_landscape()  # Horizontal
			worksheet.set_paper(9)  # A-4
			worksheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
			worksheet.fit_to_pages(1, 0)  # Ajustar por Columna

			fontSize = 10															#Antes 8
			bold = workbook.add_format(
			{'bold': True, 'font_name': 'Arial', 'font_size': fontSize})
			#normal = workbook.add_format()											#Esto creo que no hace nada...
			boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
			# boldbord.set_border(style=1)
			boldbord.set_align('center')
			boldbord.set_align('bottom')
			boldbord.set_text_wrap()
			boldbord.set_font_size(fontSize)
			boldbord.set_bg_color('#11AA66')										#Default:#99CCFF
			numberdos = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
			formatLeft = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': fontSize})
			formatLeftColor = workbook.add_format({'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'bg_color': '#99CCFF', 'font_size': fontSize})
			styleFooterSum = workbook.add_format({'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize, 'top': 1, 'bottom': 2})
			styleFooterSum.set_bottom(6)
			numberdos.set_font_size(fontSize)
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_text_wrap()
			# numberdos.set_border(style=1)

			title = workbook.add_format({'bold': True, 'font_name': 'Arial'})
			title.set_align('center')
			title.set_align('vcenter')
			# title.set_text_wrap()
			title.set_font_size(18)
			company = record.env['res.company'].search([], limit=1)[0]

			x = 0

			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			worksheet.merge_range(
				'D1:O1', u"PLANILLA DE SUELDOS Y SALARIOS", title)						#Default: D1:O1
			worksheet.set_row(x, 29)													#Default: 29
			x = x+2

			worksheet.write(x, 0, u"Empresa:", bold)
			worksheet.write(x, 1, company.name, formatLeft)

			x = x+1
			worksheet.write(x, 0, u"Mes:", bold)
			worksheet.write(
				x, 1, record.get_mes(int(record.date_end[5:7]) if record.date_end else 0).upper()+"-"+record.date_end[:4], formatLeft)

			x = x+3

			header_planilla_tabular = record.env['ir.model.fields'].search(
				[('name', 'like', 'x_%'), ('model', '=', 'planilla.tabular')], order="create_date")
			worksheet.write(x, 0, header_planilla_tabular[0].field_description, formatLeftColor)
			for i in range(1, len(header_planilla_tabular)):
				if i not in (3,4):
					worksheet.write(x, i, header_planilla_tabular[i].field_description, boldbord)
			worksheet.write(x,i+1,'Aportes ESSALUD',boldbord)
			worksheet.set_row(x, 50)

			fields = ['\"'+column.name+'\"' for column in header_planilla_tabular]
			x = x+1

			filtro = []

			query = 'select %s from planilla_tabular' % (','.join(fields))
			record.env.cr.execute(query)
			datos_planilla = record.env.cr.fetchall()
			range_row = len(datos_planilla[0] if len(datos_planilla) > 0 else 0)
			total_essalud = 0
			for i in range(len(datos_planilla)):
				for j in range(range_row):
					if j not in (3,4):
						if j == 0 or j == 1:
							worksheet.write(x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', formatLeft)
						else:
							worksheet.write(x, j, datos_planilla[i][j] if datos_planilla[i][j] else '0.00', numberdos)
				essalud = record.env['hr.payslip'].browse(datos_planilla[i][4]).essalud
				worksheet.write(x,j+1,essalud,formatLeft)
				total_essalud += essalud
				x = x+1
			x = x + 1
			datos_planilla_transpuesta = zip(*datos_planilla)

			for j in range(5, len(datos_planilla_transpuesta)):
				worksheet.write(x, j, sum([float(d) for d in datos_planilla_transpuesta[j]]), styleFooterSum)

			worksheet.write(x,j+1,total_essalud,styleFooterSum)

			# seteando tamaño de columnas
			col_widths = record.get_col_widths(datos_planilla)
			worksheet.set_column(0, 0, col_widths[0]-10)
			worksheet.set_column(1, 1, col_widths[1]-7)
			for i in range(2, len(col_widths)):
				worksheet.set_column(i, i, col_widths[i])

			worksheet.set_column('D:D',None,None,{'hidden':True})
			worksheet.set_column('E:E',None,None,{'hidden':True})

		workbook.close()

		f = open(direccion+'planilla_tabular.xls', 'rb')

		vals = {
			'output_name': 'planilla_tabular.xls',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}

	def regulariza_dias_laborados(self):
		planilla_ajustes = self.env['planilla.ajustes'].get_parametros_ajustes()
		DLAB = planilla_ajustes.cod_dias_laborados
		self.ensure_one()

		for payslip in self.slip_ids:
			dias_laborados = payslip.worked_days_line_ids.search(
				[('payslip_id', '=', payslip.id), ('code', '=', planilla_ajustes.cod_dias_laborados.codigo)])

			if payslip.contract_id.date_start > self.date_start and payslip.contract_id.date_end < self.date_end:
				fecha_ini = fields.Date.from_string(payslip.contract_id.date_start)
				fecha_fin = fields.Date.from_string(payslip.contract_id.date_end)
				if fecha_ini and fecha_fin:
					dias_laborados.number_of_days = abs(fecha_fin.day-fecha_ini.day)+1
				else:
					dias_laborados.number_of_days = abs(DLAB.dias-fecha_ini.day)+1

			elif payslip.contract_id.date_start > self.date_start:
				fecha_ini = fields.Date.from_string(payslip.contract_id.date_start)
				if fecha_ini:
					dias_laborados.number_of_days = 6-fecha_ini.day+1
			elif payslip.contract_id.date_end < self.date_end:
				if payslip.contract_id.date_end:
					fecha_fin = fields.Date.from_string(payslip.contract_id.date_end)
					if fecha_fin:
						dias_laborados.number_of_days = fecha_fin.day
				else:
					dias_laborados.number_of_days = DLAB.dias
			else:
				dias_laborados.number_of_days = DLAB.dias

			faltas = payslip.worked_days_line_ids.search([('payslip_id', '=', payslip.id), ('code', 'in', planilla_ajustes.cod_dias_subsidiados.mapped('codigo'))])
			for i in faltas:
				dias_laborados.number_of_days += -i.number_of_days

		return self.env['planilla.warning'].info(title='Resultado de generacion', message="SE GENERO DE MANERA EXITOSA!")

	@api.multi
	def exportar_planilla_tabular_total_xlsx(self):
    		
		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')

		workbook = Workbook(direccion+'planilla_tabular.xls')

		totalsheet=workbook.add_worksheet('Nomina Sumarizada')
		procesados=[]
		first=True
		totalsheet.set_landscape()  # Horizontal
		totalsheet.set_paper(9)  # A-4
		totalsheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		totalsheet.fit_to_pages(1, 0)  # Ajustar por Columna
		fontSize = 10															#Antes 8
		bold = workbook.add_format(
		{'bold': True, 'font_name': 'Arial', 'font_size': fontSize})
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		boldbord.set_align('center')
		boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(fontSize)
		boldbord.set_bg_color('#99CCFF')										#Default:#99CCFF
		numberdos = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		formatLeft = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': fontSize})
		formatLeftColor = workbook.add_format({'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'bg_color': '#99CCFF', 'font_size': fontSize})
		styleFooterSum = workbook.add_format({'bold': True, 'num_format': '0.00', 'font_name': 'Arial', 'align': 'right', 'font_size': fontSize, 'top': 1, 'bottom': 2})
		styleFooterSum.set_bottom(6)
		numberdos.set_font_size(fontSize)
		bord = workbook.add_format()
		bord.set_border(style=1)
		bord.set_text_wrap()

		title = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		title.set_align('center')
		title.set_align('vcenter')
		title.set_font_size(18)
		x = 0

		for record in self:						#Todos los empleados
			record.env['planilla.planilla.tabular.wizard'].reconstruye_tabla(record.date_start,record.date_end)
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			if first:
				company = record.env['res.company'].search([], limit=1)[0]
				totalsheet.merge_range('D1:O1', u"PLANILLA DE SUELDOS Y SALARIOS", title)						#Default: D1:O1
				totalsheet.set_row(x, 29)													#Default: 29
				x = x+2
				totalsheet.write(x, 0, u"Empresa:", bold)
				totalsheet.write(x, 1, company.name, formatLeft)
				x = x+1
				periodo=[record.date_start,record.date_end]
				for nomina in self:
					if nomina.date_start < periodo[0]:
						periodo[0]=nomina.date_start
					if nomina.date_end > periodo[1]:
						periodo[1]=nomina.date_end
				totalsheet.write(x,0, u"Periodo:", bold)
				totalsheet.write(x,1, "{}  -  {}".format(periodo[0],periodo[1]),formatLeft)
				x=x+1
				totalsheet.write(x, 0, u"Mes:", bold)
				totalsheet.write(x, 1, record.get_mes(int(record.date_end[5:7]) if record.date_end else 0).upper()+"-"+record.date_end[:4], formatLeft)
				x = x+3
				x=6	#fila del encabezado
		 		header_planilla_tabular = record.env['ir.model.fields'].search(
						[('name', 'like', 'x_%'), ('model', '=', 'planilla.tabular')], order="create_date")
				totalsheet.write(x, 0, header_planilla_tabular[0].field_description, formatLeftColor)
				total=[0.0 for f in range(len(header_planilla_tabular)+1)]
				for i in range(1, len(header_planilla_tabular)):
					if i not in (3,4):
						totalsheet.write(x, i, header_planilla_tabular[i].field_description, boldbord)
				totalsheet.write(x,i+1,'Aportes ESSALUD',boldbord)
				totalsheet.set_row(x, 50)
				fields = ['\"'+column.name+'\"' for column in header_planilla_tabular]
				first=False

			query = 'select %s from planilla_tabular' % (','.join(fields))
			record.env.cr.execute(query)
			datos_planilla = record.env.cr.fetchall()
			range_row = len(datos_planilla[0] if len(datos_planilla) > 0 else 0)
			
			for i in range(len(datos_planilla)):	#empleado a procesar
				if datos_planilla[i][1] in procesados:
					continue
				
				procesados.append(datos_planilla[i][1])
				data=[0.0 for f in range(range_row+1)]
				for k in range(3):
					data[k]=(datos_planilla[i][k] if datos_planilla[i][k] else '0.00')

				for nomina in self:					#recorrido para encontrar todas sus entradas en todas las nominas
					nomina.env['planilla.planilla.tabular.wizard'].reconstruye_tabla(record.date_start,record.date_end)
					nomina.env.cr.execute(query)
					datos_nomina = nomina.env.cr.fetchall()
					bandera2=0

					for ii in range(len(datos_nomina)):	#para encontrar sus entradas en la nomina actual
						if datos_planilla[i][1] != datos_nomina[ii][1]:
							continue
						for j in range(range_row):			#para moverse en la data
							if j not in range(4):
								data[j]+=(datos_nomina[ii][j] if datos_nomina[ii][j] else 0.00)
								total[j]+=(datos_nomina[ii][j] if datos_nomina[ii][j] else 0.00)
						essalud = record.env['hr.payslip'].browse(datos_nomina[ii][4]).essalud
						data[j+1]+=essalud
						break
				x+=1
				for i in range(len(data)):
					totalsheet.write(x, i, data[i], numberdos if type(data)==(type(0) or type(0.0)) else formatLeft)		
		
		x = x + 2

		for j in range(5, len(total)):
			totalsheet.write(x, j, total[j], styleFooterSum)

		# seteando tamaño de columnas
		col_widths = record.get_col_widths(datos_planilla)
		totalsheet.set_column(0, 0, col_widths[0]-10)
		totalsheet.set_column(1, 1, col_widths[1]-7)
		for i in range(2, len(col_widths)):
			totalsheet.set_column(i, i, col_widths[i])
		
		totalsheet.set_column('D:D',None,None,{'hidden':True})
		totalsheet.set_column('E:E',None,None,{'hidden':True})	

		workbook.close()
		f = open(direccion+'planilla_tabular.xls', 'rb')

		vals = {
			'output_name': 'planilla_tabular.xls',
			'output_file': base64.encodestring(''.join(f.readlines())),
		}

		sfs_id = self.env['planilla.export.file'].create(vals)

		return {
			"type": "ir.actions.act_window",
			"res_model": "planilla.export.file",
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
		}
	
	
	@api.multi
	def _wizard_generar_asiento_contable(self):

		total_debe = 0
		total_haber = 0

		for record in self:

			query_vista = """
				select * from (
					select
					a6.date_end as fecha_fin,
					'ASIENTO DISTRIBUIDO DE LA PLANILLA DEL MES':: TEXT as concepto,
					a7.id as cuenta_debe,
					a10.id::integer as cuenta_analitica_id,
					round(sum(a1.amount*(a9.porcentaje/100))::numeric,2) as debe,
					0 as haber,
					''::text as nro_documento,
					0 as partner_id
					from hr_payslip_line a1
					left join hr_payslip a2 on a2.id=a1.slip_id
					left join hr_contract a3 on a3.id=a1.contract_id
					left join hr_employee a4 on a4.id=a1.employee_id
					left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
					left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
					left join account_account a7 on a7.id=a5.account_debit
					left join planilla_distribucion_analitica a8 on a8.id=a3.distribucion_analitica_id
					left join planilla_distribucion_analitica_lines a9 on a9.distribucion_analitica_id=a8.id
					left join account_analytic_account a10 on a10.id=a9.cuenta_analitica_id
					where a7.code is not null and a1.amount<>0 and a6.date_start='%s' and a6.date_end='%s'
					group by a6.date_end,a7.id,a10.id
					order by a7.code)tt
				union all
				select * from (
					select
					a6.date_end as fecha_fin,
					a5.name as concepto,
					a7.id as cuenta_haber,
					0::integer as cuenta_analitica_id,
					0 as debe,
					round(sum((a1.amount))::numeric,2) as haber,
					''::text as nro_documento,
					0 as partner_id
					from hr_payslip_line a1
					left join hr_payslip a2 on a2.id=a1.slip_id
					left join hr_contract a3 on a3.id=a1.contract_id
					left join hr_employee a4 on a4.id=a1.employee_id
					left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
					left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
					left join account_account a7 on a7.id=a5.account_credit
					where a7.code is not null and a6.date_start='%s' and a6.date_end='%s'
						and a1.code not in ('COMFI','COMMIX','SEGI','A_JUB')
						and a7.code not like '%s'
					group by a6.date_end,a6.name,a5.name,a7.id,a7.code
					having sum(a1.amount)<>0
					order by a7.code)tt
				union all
				select * from (
					select
					hpr.date_end as fecha_fin,
					pa.entidad||' - '||hpl.code as concepto,
					pa.account_id as cuenta_haber,
					0::integer as cuenta_analitica_id,
					0 as debe,
					round(sum((hpl.amount))::numeric,2) as haber,
					''::text as nro_documento,
					0 as partner_id
					from hr_payslip_line hpl
					inner join hr_payslip hp on hp.id = hpl.slip_id
					inner join hr_contract hc on hc.id = hp.contract_id
					inner join planilla_afiliacion pa on pa.id = hc.afiliacion_id
					inner join hr_payslip_run hpr on hpr.id = hp.payslip_run_id
					inner join hr_salary_rule hsr on hsr.id = hpl.salary_rule_id
					where pa.account_id is not null and hpr.date_start='%s' and hpr.date_end='%s'
						and hpl.code in ('COMFI','COMMIX','SEGI','A_JUB')
					group by hpr.date_end,hpr.name,pa.entidad,pa.account_id,hpl.code
					having sum(hpl.amount)<>0
				)ttt
				union all
				select * from (
					select
					min(a6.date_end) as fecha_fin,
					min(a5.name) as concepto,
					min(a7.id) as cuenta_haber,
					0::integer as cuenta_analitica_id,
					0 as debe,
					round(sum((a1.amount))::numeric,2) as haber,
					coalesce(rp.nro_documento,'')::text as nro_documento,
					coalesce(rp.id,0) as partner_id
					from hr_payslip_line a1
					left join hr_payslip a2 on a2.id=a1.slip_id
					left join hr_contract a3 on a3.id=a1.contract_id
					left join hr_employee a4 on a4.id=a1.employee_id
					left join res_partner rp on rp.id = a4.address_home_id
					left join hr_salary_rule a5 on a5.id=a1.salary_rule_id
					left join hr_payslip_run a6 on a6.id=a2.payslip_run_id
					left join account_account a7 on a7.id=a5.account_credit
					where a7.code is not null and a6.date_start= '%s' and a6.date_end= '%s'
						and a1.code not in ('COMFI','COMMIX','SEGI','A_JUB')
						and a7.code like '%s'
					group by rp.id,rp.nro_documento,a7.code
					having sum(a1.amount)<>0
					order by a7.code)tt
						""" % (record.date_start, record.date_end,
							record.date_start, record.date_end, '41%',
							record.date_start, record.date_end,
							record.date_start, record.date_end, '41%')
			record.env.cr.execute(query_vista)

			res = record.env.cr.dictfetchall()

			for x in res:
				try:
					total_debe += x['debe']
				except:
					total_debe += 0
			for x in res:
				try:
					total_haber += x['haber']
				except:
					total_haber += 0

		var = total_debe-total_haber

		vals = {
			'total_debe': total_debe,
			'total_haber': total_haber,
			'diferencia': var
		}

		sfs_id = record.env['planilla.asiento.contable'].create(vals)

		return {
			'name': 'Asiento Contable',
			"type": "ir.actions.act_window",
			"res_model": "planilla.asiento.contable",
			'view_type': 'form',
			'view_mode': 'form',
			"views": [[False, "form"]],
			"res_id": sfs_id.id,
			"target": "new",
			'context': {'current_id': self[0].id, 'account_move_lines': res}
		}

	@api.multi
	def generar_planilla_tabular(self):
		return self[0].env['planilla.planilla.tabular.wizard'].create({'fecha_ini': self[0].date_start, 'fecha_fin': self[-1].date_end}).do_rebuild()
