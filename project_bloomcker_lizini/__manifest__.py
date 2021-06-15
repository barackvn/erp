# -*- coding: utf-8 -*-
{
    "name": """Requerimientos de Lizini""",
    "summary": """Bloomcker""",
    "description": """
    -Modificiacion de días por defecto en nóminas.
    -Adaptación de reportes para multiregistro.
    """,
    "author": "Bloomcker",
    "depends": [
        "base",
        "planilla"
    ],
    "data": [
        'views/hr_payslip_run_view_ext.xml',
        'views/hr_employee_entry_date_view.xml'
        ],
    "application": True,
}