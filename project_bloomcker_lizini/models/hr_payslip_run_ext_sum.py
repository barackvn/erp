# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import base64
import io
from xlsxwriter.workbook import Workbook
import sys
reload(sys)
sys.setdefaultencoding('iso-8859-1')
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib.pagesizes import letter
from decimal import *

class HrPayslipRunSum(models.Model):

	_inherit = 'hr.payslip.run'

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
				totalsheet.write(x,i+2,'Fecha de ingreso',boldbord)
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
				employee=record.env['hr.employee'].search([['name','like',datos_planilla[i][0]]])
				procesados.append(datos_planilla[i][1])
				data=[0.0 for f in range(range_row+2)]
				for k in range(3):
					data[k]=(datos_planilla[i][k] if datos_planilla[i][k] else '0.00')
				if employee.date_entry:
					data[range_row+1]=employee.date_entry
				else:
					data[range_row+1]=''

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
	def genera_planilla_afp_net_sumarizada(self):
		import io
		output = io.BytesIO()
		
		try:
			direccion = self.env['main.parameter.hr'].search([])[0].dir_create_file
		except:
			raise UserError('Falta configurar un directorio de descargas en el menu Configuracion/Parametros/Directorio de Descarga')
			
		workbook = Workbook(direccion + 'planilla_afp_net_sum.xls')
		
		totalsheet=workbook.add_worksheet('Nomina Sumarizada')
		procesados=[]
		totalsheet.set_landscape()  # Horizontal
		totalsheet.set_paper(9)  # A-4
		totalsheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
		totalsheet.fit_to_pages(1, 0)  # Ajustar por Columna
		fontSize = 10															#Antes 8
		boldbord = workbook.add_format({'bold': True, 'font_name': 'Arial'})
		boldbord.set_align('center')
		boldbord.set_align('bottom')
		boldbord.set_text_wrap()
		boldbord.set_font_size(fontSize)
		boldbord.set_bg_color('#99CCFF')										#Default:#99CCFF
		numberdos = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'right'})
		formatLeft = workbook.add_format({'num_format': '0.00', 'font_name': 'Arial', 'align': 'left', 'font_size': fontSize})
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
		data=[]
		
		for record in self:
            
			planilla_ajustes = record.env['planilla.ajustes'].search([], limit=1)

			for payslip_run in record.browse(record.ids):
				query_vista=""" DROP VIEW IF EXISTS planilla_afp_net_xlsx_sum;
                    create or replace view planilla_afp_net_xlsx_sum as (
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
                
				for line in record.env['planilla.afp.net.xlsx'].search([]):                             #empleado a procesar

					if line.id in procesados:
						continue
					procesados.append(line.id)

					for nomina in self:
						planilla_ajustes = nomina.env['planilla.ajustes'].search([], limit=1)
						
						for payslip_run in nomina.browse(nomina.ids):
							query_vista=""" DROP VIEW IF EXISTS planilla_afp_net_xlsx_sum;
                                create or replace view planilla_afp_net_xlsx_sum as (
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
							nomina.env.cr.execute(query_vista)

							for dato in nomina.env['planilla.afp.net.xlsx'].search([]):
								if line.id != dato.id:
									continue
								empleado=[]
								empleado.append(line.id if line.id else '')
								empleado.append(line.cuspp if line.cuspp else '')
								empleado.append(line.tipo_doc if line.tipo_doc else '')
								empleado.append(line.identification_id if line.identification_id else '')
								empleado.append(line.a_paterno)
								empleado.append(line.a_materno)
								empleado.append(line.nombres)
								empleado.append(line.relacion_laboral if line.relacion_laboral else '')
								empleado.append(line.inicio_relacion_laboral if line.inicio_relacion_laboral else '')
								empleado.append(line.cese_relacion_laboral if line.cese_relacion_laboral else '')
								empleado.append(line.excepcion_aportador if line.excepcion_aportador else '')
								empleado.append(line.remuneracion_asegurable)
								empleado.append(line.aporte_fin_provisional)
								empleado.append(line.aporte_sin_fin_provisional)
								empleado.append(line.aporte_voluntario_empleador)
								empleado.append(line.regimen_laboral if line.regimen_laboral else '')
								break

							data.append(empleado)

		ids=[]
        
		for i in range(len(data)):
			if data[i][0] in ids: continue
			ids.append(data[i][0])
			for j in range(len(data[i])):
				if j in range(11,14):
					sum=0
					for k in range(len(data)):
						if data[i][0]==data[k][0]:
							sum+=data[k][j]
					totalsheet.write(x, j, sum, numberdos)
				else:
					totalsheet.write(x, j, str(data[i][j]), formatLeft)
			x+=1

		workbook.close()

		f = open(direccion+'planilla_afp_net_sum.xls', 'rb')
		vals = {
			'output_name': 'planilla_afp_net_sum.xls',
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

	def exportar_plame_sumarizado(self):
    
		data_total=[]

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
							data_total.append(line)
					employees.append(payslip.employee_id.id)

		verif=[]
		for emp in data_total:
			if [emp['dni'],emp['sunat']] in verif:
				continue
			verif.append([emp['dni'],emp['sunat']])
			sum=[0 for x in emp]
			sum[0]=emp['tipo_doc']
			sum[1]=emp['dni']
			sum[2]=emp['sunat']
			for comparator in data_total:
				if emp['dni']==comparator['dni'] and emp['sunat']==comparator['sunat']:
					sum[3]+=comparator['monto_devengado']
					sum[4]+=comparator['monto_pagado']
			f.write('{}|{}|{}|{}|{}\r\n'.format(*sum))

		f.close()
		f = open(docname,'rb')
		vals = {
			'output_name': '0601%s%s%s.rem' % (
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
	def exportar_plame_horas_sumarizado(self):

		planilla_ajustes = self.env['planilla.ajustes'].search([], limit=1)
		data_total=[]
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
						print(data)
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
						data_total.append([data['code'],data['dni'],total_horas_jornada_ordinaria,0,horas_extra,0])
						employees.append(payslip.employee_id.id)

		verif=[]
		for emp in data_total:                  #estructura [code|dni|horas_jornada|0|horas_extra|0]
			if [emp[1],emp[0]] in verif:
				continue
			verif.append([emp[1],emp[0]])
			sum=[0 for x in emp]
			sum[0]=emp[0]
			sum[1]=emp[1]
			sum[3]=sum[5]=0
			for comparator in data_total:
				if emp[0]==comparator[0] and emp[1]==comparator[1]:
					sum[2]+=comparator[2]
					sum[4]+=comparator[4]
			f.write('{}|{}|{}|{}|{}|{}\r\n'.format(*sum))

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
	def exportar_plame_subsidios_sumarizado(self):

		data_total=[]
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
						data_total.append(data)
						employees.append(payslip.employee_id.id)

		verif=[]
		for emp in data_total:
			if [emp['dni'],emp['sunat_code'],emp['code']] in verif:
				continue
			verif.append([emp['dni'],emp['sunat_code'],emp['code']])
			sum=[0 for x in emp]
			sum[0]=emp['sunat_code']
			sum[1]=emp['dni']
			sum[2]=emp['code']
			for comparator in data_total:
				if emp['dni']==comparator['dni'] and emp['sunat_code']==comparator['sunat_code'] and emp['code']==comparator['code']:
					sum[3]+=comparator['dias']
			f.write('{}|{}|{}|{}|\r\n'.format(*sum))

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
	def exportar_plame_tasas_sumarizado(self):

		data_total=[]
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
							data_total.append([cod_sunat,dni,sctr.code,sctr.porcentaje])
							employees.append(payslip.employee_id.id)

		verif=[]
		for emp in data_total:
			if [emp[0],emp[1],emp[2]] in verif:
				continue
			verif.append([emp[0],emp[1],emp[2]])
			sum=[0 for x in emp]
			sum[0]=emp[0]
			sum[1]=emp[1]
			sum[2]=emp[2]
			for comparator in data_total:
				if emp[0]==comparator[0] and emp[1]==comparator[1] and emp[2]==comparator[2]:
					sum[3]+=comparator['dias']
			f.write('{}|{}|{}|{}|\r\n'.format(*sum))

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
	def _wizard_generar_asiento_contable_total(self):

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
			print('el valor de res es {}\n'.format(res))
			total_debe=[]
			total_haber=[]

			for x in res:
				try:
					total_debe.append(x['debe'])
				except:
					continue
			for x in res:
				try:
					total_haber.append(x['haber'])
				except:
					continue
		
		debe=haber=0
		for amount in total_debe:
			debe+=amount
		for amount in total_haber:
			haber+=amount
		var = debe-haber

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