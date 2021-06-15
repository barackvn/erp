from xmlrpc import client as xmlrpclib

info = xmlrpclib.ServerProxy('https://demo.odoo.com/start').start()
url = 'http://159.65.110.110:8069'
db = 'METATRON_PRUEBA'
username = 'admin'
password = '1234'

# url, db, username, password = \
#     info['host'], info['database'], info['user'], info['password']

common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

models = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))

id = models.execute_kw(db, uid, password, 'account.invoice', 'create',
	[{
	'name':'Factura nueva',
	'date_invoice': '2021-06-09',
	'journal_id': 1,
	'partner_id': 20,
	'fiscal_position_id': False,
	'state': 'draft',
	'type': 'out_invoice',
	'it_type_document': 9,
	}])

	# {'origin': False, 'reference': u'FPP10000012', 'debit_invoice_type': 1,
	# 'number': False, 'date_invoice': '2021-06-09',
	#  'account_ids': [(0, 0, {'igv': 450.0, 'perception': 2950.0, 'fecha': '2021-05-31', 'tipo_doc': 2, 'comprobante': u'F0010000047', 'base_imponible': 2500.0})],
	#  'partner_id': 20,
	#  'fiscal_position_id': False,
	#  'name': u'INTERES POR MORA', 'serie_id': 4, 'journal_id': 1, 'state': 'draft',
	#  'invoice_line_ids': [(0, 0, {'product_id': False, 'price_unit': 25.0, 'account_id': 3940, 'invoice_line_tax_ids': [(6, 0, [26])],
	#  'quantity': 100.0, 'name': u'PANETONES PARA SANDRA'})],
	#  'it_type_document': 9, 'type': u'out_invoice'}

print(id)
