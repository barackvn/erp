# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError

class Employee_schedule_ext(models.Model):
    
    _inherit='hr.employee'

    hora_ent_fija = fields.Datetime('Hora de Entrada', default=datetime.strptime("12:00:00", "%X").time())
    hora_sal_fija = fields.Datetime('Hora de Salida', default=datetime.strptime("20:00:00", "%X").time())


class Interconetion_payslip_ext(models.Model):
    _inherit='hr.payslip'

    def retardo_horas_extra(self):
        horas_ent_sal=self.env['hr.employee'].search([('id', '=', self.employee_id.id)])

        hora_ent_fija=fields.Datetime.from_string(horas_ent_sal.hora_ent_fija).time()
        hora_sal_fija=fields.Datetime.from_string(horas_ent_sal.hora_sal_fija).time()

        data_empleado=self.env['hr.attendance'].search([['employee_id', '=', self.employee_id.id]])
        data_nomina=self.env['hr.payslip'].search([('employee_id','=', self.employee_id.id),('payslip_run_id','=',self.payslip_run_id.id)])

        tardanza=0
        horas_ext=0
        horas_trabajadas=0
        faltas=6
        
        for dia in data_empleado:

            fecha_dia=fields.Datetime.from_string(dia.check_in).date()
            fecha_inicio=fields.Datetime.from_string(data_nomina.date_from).date()
            fecha_fin=fields.Datetime.from_string(data_nomina.date_to).date()

            if fecha_inicio < fecha_dia and fecha_dia < fecha_fin:

                hora_ent=fields.Datetime.from_string(dia.check_in).time()
                hora_sal=fields.Datetime.from_string(dia.check_out).time()

                if hora_ent > hora_ent_fija:
                    dif=(hora_ent.hour+float(hora_ent.minute)/60+float(hora_ent.second)/3600)-(hora_ent_fija.hour+float(hora_ent_fija.minute)/60+float(hora_ent_fija.second)/3600)
                    print('la diferencia en tardanza es {}'.format(dif))
                    tardanza+=dif
                if hora_sal > hora_sal_fija:
                    dif= (hora_sal.hour+float(hora_sal.minute)/60+float(hora_sal.second)/3600)-(hora_sal_fija.hour+float(hora_sal_fija.minute)/60+float(hora_sal_fija.second)/3600)
                    print('la diferencia en horas extra es {}'.format(dif))
                    horas_ext+=dif

                dif=(hora_sal.hour+float(hora_sal.minute)/60+float(hora_sal.second)/3600)-(hora_ent.hour+float(hora_ent.minute)/60+float(hora_ent.second)/3600)
                horas_trabajadas+=dif
                faltas-=1

        for days_line in data_nomina.worked_days_line_ids:
            if days_line.code == "TAR":
                days_line.number_of_days = 0#dias_tar   
                days_line.number_of_hours = int(tardanza%8)
                days_line.minutos = int((tardanza%1)*60)
            elif days_line.code == "HER":
                days_line.number_of_days = 0#dias_ext   
                days_line.number_of_hours = int(horas_ext%8)
                days_line.minutos = int((horas_ext%1)*60)
            elif days_line.code == "DLAB":
                if faltas < 1:
                    faltas=0
                days_line.number_of_days = 6-faltas
                days_line.number_of_hours = int(horas_trabajadas)
                days_line.minutos = int((horas_trabajadas%1)*60)
            elif days_line.code == "FAL":
                if faltas < 1:
                    faltas=0
                days_line.number_of_days = faltas
