# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class Employee_schedule_ext(models.Model):

    _inherit='hr.employee'

    hora_ent_fija = fields.Datetime('Hora de Entrada', default=datetime(1900,1,1,12,27,40))
    hora_sal_fija = fields.Datetime('Hora de Salida', default=datetime(1900,1,1,21,27,40))


class Interconetion_payslip_ext(models.Model):
    _inherit='hr.payslip'

    def retardo_horas_extra(self):
        horas_ent_sal=self.env['hr.employee'].search([('id', '=', self.employee_id.id)])

        hora_ent_fija=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(horas_ent_sal.hora_ent_fija)).time()
        hora_sal_fija=fields.Datetime.context_timestamp(self, fields.Datetime.from_string(horas_ent_sal.hora_sal_fija)).time()

        data_empleado=self.env['hr.attendance'].search([['employee_id', '=', self.employee_id.id]])
        data_nomina=self.env['hr.payslip'].search([('employee_id','=', self.employee_id.id),('payslip_run_id','=',self.payslip_run_id.id)])

        tardanza=0
        horas_ext=0
        horas_trabajadas=0
        worked_days=[]

        for dia in data_empleado:

            fecha_dia=fields.Datetime.from_string(dia.check_in).date()
            fecha_inicio=fields.Datetime.from_string(data_nomina.date_from).date()
            fecha_fin=fields.Datetime.from_string(data_nomina.date_to).date()

            if not(fecha_inicio <= fecha_dia and fecha_dia <= fecha_fin):
                continue
            
            cache=[]
            for entradas in data_empleado:
                fecha_entrada=fields.Datetime.from_string(entradas.check_in).date()
                if (entradas not in cache) and fecha_dia==fecha_entrada:
                    cache.append(entradas)

            if len(cache)==2:
                if fields.Datetime.context_timestamp(self,fields.Datetime.from_string(cache[0].check_in)).time() > fields.Datetime.context_timestamp(self,fields.Datetime.from_string(cache[1].check_in)).time():
                    cache=[cache[1],cache[0]]

            if cache in worked_days:
                continue
            worked_days.append(cache)
            
            date_ent=fields.Datetime.context_timestamp(self,fields.Datetime.from_string(cache[0].check_in))
            hora_ent=date_ent.time()
            if len(cache)==2:
                date_sal=fields.Datetime.context_timestamp(self,fields.Datetime.from_string(cache[1].check_out))
                date_sal_alm=fields.Datetime.context_timestamp(self,fields.Datetime.from_string(cache[0].check_out))
                date_ent_alm=fields.Datetime.context_timestamp(self,fields.Datetime.from_string(cache[1].check_in))
                hora_sal=date_sal.time()
                hora_sal_alm=date_sal_alm.time()
                hora_ent_alm=date_ent_alm.time()
    
                dif=(hora_sal_alm.hour+float(hora_sal_alm.minute)/60+float(hora_sal_alm.second)/3600)-(hora_ent.hour+float(hora_ent.minute)/60+float(hora_ent.second)/3600)
                dif+=(hora_sal.hour+float(hora_sal.minute)/60+float(hora_sal.second)/3600)-(hora_ent_alm.hour+float(hora_ent_alm.minute)/60+float(hora_ent_alm.second)/3600)
                horas_trabajadas+=dif

            else:
                date_sal=fields.Datetime.context_timestamp(self,fields.Datetime.from_string(cache[0].check_out))
                hora_sal=date_sal.time()
                dif=(hora_sal.hour+float(hora_sal.minute)/60+float(hora_sal.second)/3600)-(hora_ent.hour+float(hora_ent.minute)/60+float(hora_ent.second)/3600)
                horas_trabajadas+=dif

            delta1=datetime(1999,1,1,hora_ent_fija.hour,hora_ent_fija.minute,hora_ent_fija.second)-datetime(1999,1,1,hora_ent.hour,hora_ent.minute,hora_ent.second)
            delta1=delta1.total_seconds()-1660
            delta2=datetime(1999,1,1,hora_sal.hour,hora_sal.minute,hora_sal.second)-datetime(1999,1,1,hora_sal_fija.hour,hora_sal_fija.minute,hora_sal_fija.second)
            delta2=delta2.total_seconds()+1660



            print("delta1",delta1)
            if delta1 <= 0:
                dif=(hora_ent.hour+float(hora_ent.minute)/60+float(hora_ent.second)/3600)-(hora_ent_fija.hour+float(hora_ent_fija.minute-27)/60+float(hora_ent_fija.second-40)/3600)
                tardanza+=dif
            print("delta2",delta2)
            if delta2 >= 0:
                dif= (hora_sal.hour+float(hora_sal.minute)/60+float(hora_sal.second)/3600)-(hora_sal_fija.hour+float(hora_sal_fija.minute-27)/60+float(hora_sal_fija.second-40)/3600)
                horas_ext+=dif


        for days_line in data_nomina.worked_days_line_ids:
            if days_line.code == "TAR":
                days_line.number_of_days = 0#dias_tar
                days_line.number_of_hours = int(tardanza)
                days_line.minutos = int((tardanza%1)*60)
            elif days_line.code == "HER":
                days_line.number_of_days = 0#dias_ext
                days_line.number_of_hours = int(horas_ext)
                days_line.minutos = int((horas_ext%1)*60)
            elif days_line.code == "DLAB":
                days_line.number_of_days = len(worked_days)
                days_line.number_of_hours = int(horas_trabajadas)
                days_line.minutos = int((horas_trabajadas%1)*60)
            elif days_line.code == "FAL":
                faltas=6-len(worked_days)
                if faltas < 1:
                    faltas=0
                days_line.number_of_days = faltas