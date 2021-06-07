# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError
import base64
from xlsxwriter.workbook import Workbook
import sys
reload(sys)
sys.setdefaultencoding('iso-8859-1')
from decimal import *


class HrPlanillaAFP(models.Model):

    _inherit = 'hr.payslip.run'

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
        first=True
        totalsheet.set_landscape()  # Horizontal
        totalsheet.set_paper(9)  # A-4
        totalsheet.set_margins(left=0.75, right=0.75, top=1, bottom=1)
        totalsheet.fit_to_pages(1, 0)  # Ajustar por Columna
        fontSize = 10															#Antes 8
        bold = workbook.add_format({'bold': True, 'font_name': 'Arial', 'font_size': fontSize})
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
                    ############################################################# Aqui empieza la locura
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
