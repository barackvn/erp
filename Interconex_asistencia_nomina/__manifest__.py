# -*- coding: utf-8 -*-
{
    "name": """Interconexion Bloomcker Asistencia y Nomina""",
    "summary": """Bloomcker""",
    "description": """Modulo para la Interconexión entre el modulo de asistencia y el módulo de nómina""",
    "author": "Carlos J Márquez",
    "depends": [
        "base",
        "planilla",
        "hr_attendance"
    ],
    "data": [
        'views/interconexion_view.xml',
        'views/horas_ent_sal_view.xml'
   ],
    "application": True,
}