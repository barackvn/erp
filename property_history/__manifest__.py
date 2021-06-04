# -*- encoding: utf-8 -*-
{
	"name": """Modulo Requerimientos de Lizini""",
    "summary": """Summary""",
    "description": """Tabla intermedia para Lizini""",
    "author": "Mario Avila",
	"depends": ['base','property_management'],
	"data":	[
        'views/property_history.xml',
        'views/assets.xml',
        'security/security.xml'
    ],
	"qweb":[
        'static/src/xml/property.xml',
    ],
    "application": True,
}
