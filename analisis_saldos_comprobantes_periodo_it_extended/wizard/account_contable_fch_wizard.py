# -*- encoding: utf-8 -*-

from openerp.osv import osv
import base64
from openerp import models, fields, api
import codecs
import pprint
from datetime import *
from odoo.exceptions import UserError, ValidationError

class account_account(models.Model):
	_inherit = 'account.account'

	analisis_documento = fields.Boolean('Analisis por Documento')


class account_contable_fch_wizard(models.TransientModel):
	_inherit='account.contable.fch.wizard'


	type_account = fields.Selection( [('A pagar','A pagar'),('A cobrar','A cobrar'),('Otros','Otras Cuentas')], 'Tipo')	




	@api.onchange('type_account')
	def _onchange_type_account(self):
		if self.type_account:
			if str(self.type_account) == "A pagar":
				return {'domain':{'cuenta':[('user_type_id.type','=','payable')]}}
			elif str(self.type_account) == "A cobrar":
				return {'domain':{'cuenta':[('user_type_id.type','=','receivable')]}}
			elif str(self.type_account) == 'Otros':
				return {'domain':{'cuenta':[('analisis_documento','=',True)]}}
		else:
			return {'domain':{'cuenta':[('user_type_id.type','in',('payable','receivable'))]}}


	@api.multi
	def do_rebuild(self):
		
		tipef = self.type_account
		cont_txt = ''
		con_elem = 0


		if self.partner_id:
			cont_txt += ( ' and ' if con_elem > 0 else ' ') + "partner = '" + self.partner_id.name + "' "
			con_elem += 1
			#filtro.append( ('partner','=',self.partner_id.name) )

		cuenta_txt = ' '

		if self.cuenta_id:
			cuenta_txt = " and cuentas.code = '" + self.cuenta_id.code + "' "
			#filtro.append( ('cuenta','=',self.cuenta_id.code) )

		tipo_filtro_def = " aat.type='payable' or aat.type='receivable' "
		if str(tipef) == 'A pagar':
			tipo_filtro_def = " aat.type='payable' "
			#filtro.append( ('tipofiltro','=','payable') )
		if str(tipef) == 'A cobrar':
			tipo_filtro_def = " aat.type='receivable' "
			#filtro.append( ('tipofiltro','=','receivable') )

		if str(tipef) == 'Otros':
			tipo_filtro_def = " cuentas.analisis_documento = true "

		if self.pendiente:
			cont_txt += ( ' and ' if con_elem > 0 else ' ') + "saldo_filter != 0 "
			con_elem += 1
			#filtro.append( ('saldo_filter','!=',0) )

		if con_elem > 0:
			cont_txt = ' where ' + cont_txt


		self.env.cr.execute(""" 

			DROP VIEW IF EXISTS account_contable_period;
			create or replace view account_contable_period as (

select * from ( 
select 
t0.id ,
t0.ide,
t4.code as periodo,
t5.code as libro,
t2.name as voucher,
t6.name as partner,
t6.nro_documento as ruc,
t7.code as type_document,
trim(t0.nro_comprobante) as comprobante,
t3.code as cuenta,
t2.date as fecha,

--ai.date_due as fecha_vencimiento,
f_final.fin as fecha_vencimiento,

t0.debit as debe,
t0.credit as haber,
t1.saldo as saldo_filter,
aat.type as tipofiltro
from 
(
select ab.id,concat(ab.partner_id,'-',ab.account_id,'-',ab.type_document_it,'-',TRIM(ab.nro_comprobante) )as ide,ab.move_id,ab.partner_id,ab.account_id,ab.type_document_it,ab.nro_comprobante,ab.debit,ab.credit from account_move_line ab
left join account_account cuentas on cuentas.id=ab.account_id
left join account_account_type aat on aat.id = cuentas.user_type_id
left join account_move am on ab.move_id = am.id
left join account_period ap on ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable and am.fecha_special = ap.special
where ( """ +tipo_filtro_def+ """ )  --and cuentas.reconcile=TRUE  
""" +cuenta_txt+ """
-------------- colocar en estas lineas la condicion de los periodos inicial y final ------------------------------
and (ap.id in (select id from account_period where periodo_num(code)>= periodo_num('""" + self.period_ini.code +"""') and periodo_num(code) <= periodo_num('""" + self.period_end.code + """') ) ) 

----------------------------------------------------------------------------------------------------

) t0


left join (

select concat(xx.partner_id,'-',xx.account_id,'-',xx.type_document_it,'-',TRIM(xx.nro_comprobante)) as ide,sum(debit)-sum(credit) as saldo from account_move_line xx
left join account_account cuentas on cuentas.id=xx.account_id
left join account_account_type aat on aat.id = cuentas.user_type_id
left join account_move am on am.id = xx.move_id
left join account_period ap on ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable and am.fecha_special = ap.special
where ( """ +tipo_filtro_def+ """ ) --and cuentas.reconcile=TRUE  
""" +cuenta_txt+ """

-------------- colocar en estas lineas la condicion de los periodos  inicial y final ------------------------------
and ( periodo_num(ap.code)>= periodo_num('""" + self.period_ini.code +"""') and periodo_num(ap.code) <= periodo_num('""" + self.period_end.code + """') )

----------------------------------------------------------------------------------------------------

group by concat(xx.partner_id,'-',xx.account_id,'-',xx.type_document_it,'-',TRIM(xx.nro_comprobante))

) t1 on t1.ide=t0.ide
left join (
select am.id,concat(aml.partner_id,'-',aml.account_id,'-',aml.type_document_it,'-',TRIM(aml.nro_comprobante) )as ide, max(aml.date_maturity) as fin from
account_move am 
inner join account_move_line aml on aml.move_id = am.id 
group by am.id,concat(aml.partner_id,'-',aml.account_id,'-',aml.type_document_it,'-',TRIM(aml.nro_comprobante)) 
) as f_final on f_final.id = t0.move_id and f_final.ide = t1.ide

left join account_move t2 on t2.id=t0.move_id
left join account_account t3 on t3.id=t0.account_id
left join account_account_type aat on aat.id = t3.user_type_id
left join account_period t4 on t4.date_start <= t2.fecha_contable and t4.date_stop >= t2.fecha_contable and t2.fecha_special = t4.special
left join account_journal t5 on t5.id=t2.journal_id 
left join res_partner t6 on t6.id=t0.partner_id
left join einvoice_catalog_01 t7 on t7.id=t0.type_document_it

left join account_invoice ai on ai.move_id = t2.id
order by partner,cuenta,type_document,comprobante,fecha
)TT """ + cont_txt + """
			)""")


		move_obj = self.env['account.contable.period']
		filtro = []


		lstidsmove= move_obj.search(filtro)
		
		if (len(lstidsmove) == 0):
			raise osv.except_osv('Alerta','No contiene datos.')

		#DSC_Exportar a CSV por el numero de filas
		self.env.cr.execute("""select count(*)  from account_contable_period""")
		rows = self.env.cr.fetchone()
		#if self.type_show == 'excel' and rows[0] > 1000:
		#	self.type_show = 'csv'
		
		if self.type_show == 'pantalla':			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'account.contable.period',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		#DSC_
		if self.type_show == 'csv':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			docname = 'CuentaCorriente.csv'
			#CSV
			sql_query = """	COPY (SELECT * FROM account_contable_period )TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			self.env.cr.execute(sql_query)
			#Caracteres Especiales
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			f = open(direccion + docname, 'rb')			
			vals = {
				'output_name': docname,
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}
			sfs_id = self.env['export.file.save'].create(vals)
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}

		if self.type_show == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			workbook = Workbook( direccion + 'tempo_cuentacorriente.xlsx')
			worksheet = workbook.add_worksheet("Cuenta Corriente")
			#Print Format
			worksheet.set_landscape() #Horizontal
			worksheet.set_paper(9) #A-4
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


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(20)
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_text_wrap()
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)			
			x= 5				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')


			worksheet.merge_range(0,0,0,11,"Cuenta Corriente",title)

			worksheet.write(1,0, "Cuenta Corriente:", bold)
			
			worksheet.write(1,1, self.period_ini.name, normal)
			
			worksheet.write(1,2, self.period_end.name, normal)
			
			worksheet.write(2,0, "Fecha:",bold)
			
			#worksheet.write(1,1, total.date.strftime('%Y-%m-%d %H:%M'),bord)
			import datetime
			worksheet.write(2,1, str(datetime.datetime.today())[:10], normal)
			

			worksheet.write(4,0, "Periodo",boldbord)
			
			worksheet.write(4,1, "Libro",boldbord)
			worksheet.write(4,2, "Voucher",boldbord)
			worksheet.write(4,3, u"RUC",boldbord)

			worksheet.write(4,4, u"Partner",boldbord)
			worksheet.write(4,5, "Tipo Doc.",boldbord)

			worksheet.write(4,6, u"Comprobante",boldbord)
			worksheet.write(4,7, u"Fecha de Emision",boldbord)
			worksheet.write(4,8, u"Fecha de Vencimiento",boldbord)
			worksheet.write(4,9, u"Cuenta",boldbord)
			worksheet.write(4,10, u"Debe",boldbord)
			worksheet.write(4,11, u"Haber",boldbord)
			worksheet.write(4,12, u"Saldo.",boldbord)


			for line in lstidsmove:
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.libro if line.libro  else '',bord )
				worksheet.write(x,2,line.voucher if line.voucher  else '',bord)
				worksheet.write(x,3,line.ruc if line.ruc else '',bord)
				worksheet.write(x,4,line.partner if line.partner else '',bord)
				worksheet.write(x,5,line.type_document if line.type_document else '',bord)
				worksheet.write(x,6,line.comprobante if line.comprobante else '',bord)
				worksheet.write(x,7,line.fecha if line.fecha  else '',bord)
				
				worksheet.write(x,8,line.fecha_vencimiento if line.fecha_vencimiento  else '',bord)
				
				worksheet.write(x,9,line.cuenta if line.cuenta  else '',bord)
				worksheet.write(x,10,line.debe ,numberdos)
				worksheet.write(x,11,line.haber ,numberdos)
				worksheet.write(x,12,line.saldo ,numberdos)
				
				x = x +1

			tam_col = [16,10,10,13,45,7,13,14,14,11,11,11,8,11,9,10]
			worksheet.set_row(0, 30)

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

			workbook.close()
			
			f = open(direccion + 'tempo_cuentacorriente.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'CuentaCorriente.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			sfs_id = self.env['export.file.save'].create(vals)
			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}

		


class saldo_comprobante_periodo_wizard(models.TransientModel):
	_inherit='saldo.comprobante.periodo.wizard'

	tipo = fields.Selection( [('A pagar','A pagar'),('A cobrar','A cobrar'),('Otros','Otras Cuentas')], 'Tipo')	



	@api.onchange('tipo')
	def _onchange_type_account(self):
		if self.tipo:
			if str(self.tipo) == "A pagar":
				return {'domain':{'cuenta':[('user_type_id.type','=','payable')]}}
			elif str(self.tipo) == "A cobrar":
				return {'domain':{'cuenta':[('user_type_id.type','=','receivable')]}}
			elif str(self.tipo) == 'Otros':
				return {'domain':{'cuenta':[('analisis_documento','=',True)]}}
		else:
			return {'domain':{'cuenta':[('user_type_id.type','in',('payable','receivable'))]}}


	@api.onchange('cuenta')
	def onchange_cuenta(self):
		if self.cuenta.id and self.cuenta.analisis_documento:
			self.tipo = 'Otros'
			

	@api.multi
	def do_rebuild(self):		

		self.env.cr.execute("""  DROP VIEW IF EXISTS saldo_comprobante_periodo;
			create or replace view saldo_comprobante_periodo as (

			select * from
			(
				select 
				aml.id as id,
				ap.name as periodo,
				am.date as fecha_emision,
				--facturas.date_due as fecha_venci,
				f_final.fin as fecha_venci,
				rp.nro_documento as ruc,
				rp.name as empresa,
				CASE WHEN aat.type= 'payable' THEN 'A pagar'  ELSE 'A cobrar' END as tipo_cuenta,
				aa.code,
				itd.code as tipo,
				TRIM(aml.nro_comprobante) as nro_comprobante,
				T.debe,
				T.haber,				
				CASE WHEN abs(T.saldo) < 0.01 then 0 else T.saldo end as saldo,
				rc.name as divisa,
				T.amount_currency,
				am.name as voucher,
				T.aml_ids,
				CASE WHEN aml.tc is not null and aml.tc != 0.0 then aml.tc else rcr.type_sale end as tc,
				rpi.name as vendedor
				from (
				select concat(account_move_line.partner_id,'-',account_id,'-',type_document_it,'-',TRIM(nro_comprobante) ) as identifica,min(account_move_line.id),sum(debit)as debe,sum(credit) as haber, sum(debit)-sum(credit) as saldo, sum(amount_currency) as amount_currency, array_agg(account_move_line.id) as aml_ids from account_move_line
				inner join account_move ami on ami.id = account_move_line.move_id
				inner JOIN account_period api ON api.date_start <= ami.fecha_contable and api.date_stop >= ami.fecha_contable  and api.special = ami.fecha_special

				left join account_account on account_account.id=account_move_line.account_id
				left join account_account_type aat on aat.id = account_account.user_type_id
				where --account_account.reconcile = true and 
				""" + ( ("""(aat.type='receivable' or aat.type='payable' )""") if self.tipo != 'Otros' else ("""( account_account.analisis_documento= true )""")  ) + """ and ami.state != 'draft'
				and periodo_num(api.code) >= periodo_num('""" + str(self.periodo_ini.code) + """') and periodo_num(api.code) <= periodo_num('""" + str(self.periodo_fin.code) + """')
				group by identifica) as T
				inner join account_move_line aml on aml.id = T.min
				inner join account_move am on am.id = aml.move_id
				inner JOIN account_period ap ON ap.date_start <= am.fecha_contable and ap.date_stop >= am.fecha_contable  and ap.special = am.fecha_special
				left join (
select concat(aml.partner_id,'-',aml.account_id,'-',aml.type_document_it,'-',TRIM(aml.nro_comprobante) )as ide, max(aml.date_maturity) as fin, am.id from
account_move am 
inner join account_move_line aml on aml.move_id = am.id 
group by am.id,concat(aml.partner_id,'-',aml.account_id,'-',aml.type_document_it,'-',TRIM(aml.nro_comprobante) )
) as f_final on f_final.ide = T.identifica and am.id = f_final.id

				left join res_partner rp on rp.id = aml.partner_id
				left join einvoice_catalog_01 itd on itd.id = aml.type_document_it
				left join res_currency rc on rc.id = aml.currency_id
				left join res_currency_rate rcr on rcr.currency_id = (select id from res_currency where name = 'USD') and rcr.name = am.date
				left join account_account aa on aa.id = aml.account_id
				left join account_account_type aat on aat.id = aa.user_type_id
				left join (select concat(partner_id,account_id,it_type_document,TRIM(reference) ) as identifica,date,date_due from account_invoice) facturas on facturas.identifica=t.identifica
				left join account_invoice ai on ai.move_id = am.id
				left join res_users ru on ru.id = ai.user_id
				left join res_partner rpi on rpi.id = ru.partner_id
				order by empresa, code, nro_comprobante
				) T
			)"""
		)
		filtro = []
		if self.check== True:
			filtro.append( ('saldo','!=',0) )
		if self.cuenta.id:
			filtro.append( ('code','=', self.cuenta.code ) )

		if self.empresa.id:
			filtro.append( ('empresa','=', self.empresa.name ) )

		if self.tipo and self.tipo != 'Otros':
			filtro.append( ('tipo_cuenta','=',self.tipo) )

		if self.comprobantes:
			lstcomprobantes = self.comprobantes.split(',')
			filtro.append( ('nro_comprobante','in',lstcomprobantes) )

		move_obj = self.env['saldo.comprobante.periodo']
		lstidsmove= move_obj.search(filtro)		
		if (len(lstidsmove) == 0) and self.mostrar != 'newwindow':
			raise osv.except_osv('Alerta','No contiene datos.')		

		##DSC_Exportar a CSV por el numero de filas
		self.env.cr.execute("""select count(*)  from saldo_comprobante_periodo""")
		rows = self.env.cr.fetchone()
		#if self.mostrar == 'excel' and rows[0] > 1000:
		#	self.mostrar = 'csv'

		if self.mostrar == 'pantalla':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'saldo.comprobante.periodo',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
			}

		if self.mostrar == 'newwindow':
			mod_obj = self.env['ir.model.data']
			act_obj = self.env['ir.actions.act_window']			
			return {
				'domain' : filtro,
				'type': 'ir.actions.act_window',
				'res_model': 'saldo.comprobante.periodo',
				'view_mode': 'tree',
				'view_type': 'form',
				'views': [(False, 'tree')],
				"target": "new",
			}

		#DSC_
		if self.mostrar == 'csv':
			direccion = self.env['main.parameter'].search([])[0].dir_create_file
			docname = 'SaldoPeriodo.csv'
			#CSV
			sql_query = """	COPY (SELECT * FROM saldo_comprobante_periodo )TO '"""+direccion+docname+"""'   WITH DELIMITER ',' CSV HEADER			
							"""
			self.env.cr.execute(sql_query)
			#Caracteres Especiales
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')
			f = open(direccion + docname, 'rb')			
			vals = {
				'output_name': docname,
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}
			sfs_id = self.env['export.file.save'].create(vals)
			return {
				"type": "ir.actions.act_window",
				"res_model": "export.file.save",
				"views": [[False, "form"]],
				"res_id": sfs_id.id,
				"target": "new",
			}

			
		if self.mostrar == 'excel':
			import io
			from xlsxwriter.workbook import Workbook
			output = io.BytesIO()
			########### PRIMERA HOJA DE LA DATA EN TABLA
			#workbook = Workbook(output, {'in_memory': True})

			direccion = self.env['main.parameter'].search([])[0].dir_create_file

			workbook = Workbook(direccion +'saldoperiodo.xlsx')
			worksheet = workbook.add_worksheet("Analisis Saldo x Periodo")
			#Print Format
			worksheet.set_landscape() #Horizontal
			worksheet.set_paper(9) #A-4
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
			numbertres = workbook.add_format({'num_format':'0.000'})
			numberdos = workbook.add_format({'num_format':'0.00'})
			bord = workbook.add_format()
			bord.set_border(style=1)
			bord.set_text_wrap()
			numberdos.set_border(style=1)
			numbertres.set_border(style=1)	


			title = workbook.add_format({'bold': True})
			title.set_align('center')
			title.set_align('vcenter')
			title.set_text_wrap()
			title.set_font_size(20)
			worksheet.set_row(0, 30)

			x= 10				
			tam_col = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			tam_letra = 1.2
			import sys
			reload(sys)
			sys.setdefaultencoding('iso-8859-1')

			worksheet.merge_range(0,0,0,11, u"Análisis de Saldos x Periodo", title)

			worksheet.write(1,0, u"Año Fiscal", bold)
			worksheet.write(1,1, self.fiscal_id.name, normal)

			worksheet.write(2,0, u"Periodo Inicial", bold)
			worksheet.write(2,1, self.periodo_ini.name, normal)

			worksheet.write(3,0, u"Periodo Final", bold)
			worksheet.write(3,1, self.periodo_fin.name, normal)

			worksheet.write(4,0, u"Solo Pendientes", bold)
			worksheet.write(4,1, 'Si' if self.check else 'No', normal)

			worksheet.write(5,0, u"Empresa", bold)
			worksheet.write(5,1, self.empresa.name if self.empresa.name else '', normal)

			worksheet.write(6,0, u"Cuenta", bold)
			worksheet.write(6,1, self.cuenta.name if self.cuenta.name else '', normal)

			worksheet.write(7,0, u"Tipo", bold)
			worksheet.write(7,1, self.tipo if self.tipo else '', normal)


			worksheet.write(9,0, u"Periodo",boldbord)
			worksheet.write(9,1, u"Fecha Emisión",boldbord)
			worksheet.write(9,2, u"Empresa",boldbord)
			worksheet.write(9,3, u"Tipo Cuenta",boldbord)
			worksheet.write(9,4, u"Cuenta",boldbord)
			worksheet.write(9,5, u"Tipo Documento",boldbord)
			worksheet.write(9,6, u"Nro. Comprobante",boldbord)
			worksheet.write(9,7, u"Debe",boldbord)
			worksheet.write(9,8, u"Haber",boldbord)
			worksheet.write(9,9, u"Saldo",boldbord)
			worksheet.write(9,10, u"Divisa",boldbord)
			worksheet.write(9,11, u"T.C.",boldbord)
			worksheet.write(9,12, u"Importe",boldbord)
			worksheet.write(9,13, u"Fecha_vencimiento",boldbord)
			worksheet.write(9,14, u"Ruc",boldbord)



			for line in self.env['saldo.comprobante.periodo'].search(filtro):
				worksheet.write(x,0,line.periodo if line.periodo else '' ,bord )
				worksheet.write(x,1,line.fecha_emision if line.fecha_emision  else '',bord )
				worksheet.write(x,2,line.empresa if line.empresa  else '',bord)
				worksheet.write(x,3,line.tipo_cuenta if line.tipo_cuenta  else '',bord)
				worksheet.write(x,4,line.code if line.code  else '',bord)
				worksheet.write(x,5,line.tipo if line.tipo  else '',bord)
				worksheet.write(x,6,line.nro_comprobante if line.nro_comprobante  else '',bord)
				worksheet.write(x,7,line.debe ,numberdos)
				worksheet.write(x,8,line.haber ,numberdos)
				worksheet.write(x,9,line.saldo ,numberdos)
				worksheet.write(x,10,line.divisa if  line.divisa else '',bord)
				worksheet.write(x,11,line.tc ,numbertres)
				worksheet.write(x,12,line.amount_currency ,numberdos)
				worksheet.write(x,13,line.fecha_venci if line.fecha_venci  else '',bord)
				worksheet.write(x,14,line.ruc if line.ruc  else '',bord)
				

				x = x +1

			tam_col = [15,11,45,9,25,12,13,11,10,14,14,10,14,13,14,10,16,16,20,36]


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
			worksheet.set_column('N:N', tam_col[13])
			worksheet.set_column('O:O', tam_col[14])
			worksheet.set_column('P:P', tam_col[15])
			worksheet.set_column('Q:Q', tam_col[16])
			worksheet.set_column('R:R', tam_col[17])
			worksheet.set_column('S:S', tam_col[18])
			worksheet.set_column('T:T', tam_col[19])

			workbook.close()
			
			f = open(direccion + 'saldoperiodo.xlsx', 'rb')
			
			
			sfs_obj = self.pool.get('repcontab_base.sunat_file_save')
			vals = {
				'output_name': 'SaldoPeriodo.xlsx',
				'output_file': base64.encodestring(''.join(f.readlines())),		
			}

			sfs_id = self.env['export.file.save'].create(vals)

			#import os
			#os.system('c:\\eSpeak2\\command_line\\espeak.exe -ves-f1 -s 170 -p 100 "Se Realizo La exportación exitosamente Y A EDWARD NO LE GUSTA XDXDXDXDDDDDDDDDDDD" ')

			return {
			    "type": "ir.actions.act_window",
			    "res_model": "export.file.save",
			    "views": [[False, "form"]],
			    "res_id": sfs_id.id,
			    "target": "new",
			}


		