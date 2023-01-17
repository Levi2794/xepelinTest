# -*- coding: utf-8 -*-

from io import BytesIO, StringIO
from odoo import http
from odoo.http import content_disposition, request
from odoo.tools.misc import xlsxwriter
import zipfile
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class GenerateFileController(http.Controller):

   def create_or_update_config(self, config_name, config_value):
      config = request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=', config_name)], limit=1)
      if config.value != False:
         config.write({
            'name': config_name,
            'value': config_value
         })
         return
      request.env['xepelinpaymentrequest.config'].sudo().create({
         'name': config_name,
         'value': config_value
      })

   def get_next_file_number(self, date, international):
      #Obtenemos la fecha del ultimo archivo creado
      file_date_config =  request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=','mx_file_date')], limit=1)
      if file_date_config.value != date:
         file_number = 0
         self.create_or_update_config('mx_file_date', date)
         self.create_or_update_config('generated_international_file_number_config', file_number)
         self.create_or_update_config('generated_local_file_number_config', file_number)
      
      #Obtenemos el numero correlativo del archivo generado
      generated_file_number_config = "generated_international_file_number_config" if international else "generated_local_file_number_config"
      generated_file_number =  request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=',generated_file_number_config)], limit=1)

      #Aumentamos al siguiente
      next_generated_file_number = int(generated_file_number.value) + 1
      #Almacenamos el nuevo valor
      generated_file_number.write({
         'value': next_generated_file_number
      })
      return next_generated_file_number

   def get_payments_request_by_ids(self, payments_request_ids, country_code, currency_name):
      return request.env['xepelinpaymentrequest.paymentrequest'].sudo().search([
         ('id', 'in', payments_request_ids),
         ('country_id.code', '=', country_code),
         ('currency_id.name', '=', currency_name),
         ('state', '=', 'approved')
      ])

   def generate_xls_santander_cl_value(self, datetime, payments_request_cl):
      if len(payments_request_cl) == 0:
         _logger.info('No hay solicitudes a procesar')
         return

      filename = 'santander_pagos_%s.xlsx' % datetime.strftime("%Y%m%d%H%M%S")
      content = []
      
      #Header
      header = [
                  'Cuenta Origen',
                  'Moneda Cuenta Origen',
                  'Cuenta Destino',
                  'Moneda Cuenta Destino',
                  'Código Banco',
                  'Rut Beneficiario',
                  'Nombre Beneficiario',
                  'Monto Transferencia',
                  'Glosa Transferencia',
                  'Dirección Correo Beneficiario',
                  'Glosa Correo Beneficiario'
               ]

      content.append(header)

      # Obtenemos el numero de cuenta de origen
      source_santander_account =  request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=','santander_account')], limit=1)
      if source_santander_account == None:
         _logger.error('La cuenta de origen no fue configurada')
      
      # Obtenemos el email para notificar los pagos
      notification_email =  request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=','notification_email')], limit=1)
      if notification_email == None:
         _logger.error('El email de notificacion no fue configurado')

      #Rows
      for payment_request_cl in payments_request_cl:
         bank_name = payment_request_cl['bank_name']
         bank = request.env['xepelinpaymentrequest.bank'].sudo().search(
            [
               ('name', '=', bank_name),
               ('country_id.code', '=', 'CL')
            ]
         , limit=1)
         
         if bank.code == False:
            _logger.error("No se pudo obtener el codigo del banco %s" % bank_name)

         reference_id = 'TES-%s'% payment_request_cl['id']

         content.append([int(source_santander_account.value), #Cuenta Origen
         payment_request_cl['currency_id'].name, #Moneda Cuenta Origen
         int(payment_request_cl['beneficiary_account_number']), #Cuenta Destino
         payment_request_cl['currency_id'].name, #Moneda Cuenta Destino
         int(bank.code), #Código Banco
         int(payment_request_cl['beneficiary_identifier']), #Rut Beneficiario
         str(payment_request_cl['beneficiary_name']), #Nombre Beneficiario
         int(payment_request_cl['total_amount']), #Monto Transferencia 
         reference_id, #Glosa Transferencia
         notification_email.value, #Dirección Correo Beneficiario
         reference_id] #Glosa Correo Beneficiario
         )
      
      xls_output = BytesIO()
      workbook =xlsxwriter.Workbook(xls_output)
      worksheet = workbook.add_worksheet()

      number_row = 0
      number_col = 0

      for row in (content):
         #Cuenta Origen
         worksheet.write(number_row, number_col, row[0])
         #Moneda Cuenta Origen
         worksheet.write(number_row, number_col + 1, row[1])
         #Cuenta Destino
         worksheet.write(number_row, number_col + 2, row[2])
         #Moneda Cuenta Destino
         worksheet.write(number_row, number_col + 3, row[3])
         #Código Banco
         worksheet.write(number_row, number_col + 4, row[4])
         #Rut Beneficiario
         worksheet.write(number_row, number_col + 5, row[5])
         # Nombre Beneficiario
         worksheet.write(number_row, number_col + 6, row[6])
         # Monto Transferencia 
         worksheet.write(number_row, number_col + 7, row[7])
         # Glosa Transferencia
         worksheet.write(number_row, number_col + 8, row[8])
         # Dirección Correo Beneficiario
         worksheet.write(number_row, number_col + 9, row[9])
         # Glosa Correo Beneficiario
         worksheet.write(number_row, number_col + 10, row[10])

         number_row += 1

      workbook.close()
      return [filename, xls_output.getvalue()]

   def generate_xls_ve_por_mas_mx_value(self, datetime, payments_request, international):
      if len(payments_request) == 0:
         _logger.info('No hay solicitudes para mx a procesar')
         return
      
      # Obtenemos el numero de cuenta de retiro
      name_retirement_account_number_config = "international_retirement_account_number_mx" if international else "local_retirement_account_number_mx"
      retirement_account_number =  request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=', name_retirement_account_number_config)], limit=1)
      if retirement_account_number == None:
         _logger.error('El numero de cuenta de retiro no fue configurada para la moneda MXN')
      
      # Obtenemos el numero de cliente
      name_international_cliente_number_config = "international_cliente_number_mx" if international else "local_cliente_number_mx"
      cliente_number =  request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=', name_international_cliente_number_config)], limit=1)
      if cliente_number == None:
         _logger.error('El numero de cliente no fue configurado para la moneda')

      # Obtenemos la comision
      name_commission_config = "international_commission_mx" if international else "local_commission_mx"
      commission_mx =  request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=', name_commission_config)], limit=1)
      if commission_mx == None:
         _logger.error('No se pudo obtener la comsion del banco Ve por mas')

      # Obtenemos el email para notificar los pagos
      notification_email =  request.env['xepelinpaymentrequest.config'].sudo().search([('name', '=','notification_email')], limit=1)
      if notification_email == None:
         _logger.error('El email de notificacion no fue configurado')

      #Fecha actual
      date = datetime.strftime("%Y%m%d")

      #Numero de archivo
      file_number = str(self.get_next_file_number(date, international)).zfill(3)

      body = ''
      tab = '\t'
      enter = '\n'

      for payment_request in payments_request:
         row = [retirement_account_number.value, # Cuenta cargo
         date, #Fecha
         payment_request['beneficiary_name'], # Nombre del beneficiario
         payment_request['beneficiary_identifier'], #RFC Beneficiario
         payment_request['beneficiary_account_number'], #Clabe del beneficiario
         str(payment_request['total_amount']).replace(".", ","), #Monto
         str(commission_mx.value).replace(".", ","), #Comision
         payment_request['concept'], #Concepto
         notification_email.value, #Correo
         ("%s%s%s" % (cliente_number.value, date, file_number))] #Agrupador
         body = body + tab.join(row) + enter
      
      txt_output = StringIO()
      txt_output.write(body)
      extension =  "05" if international else "01"
      filename = '%s.%s.%s.%s' % (cliente_number.value, date, file_number ,extension)

      return [filename, txt_output.getvalue()]

   def generate_zip_value(self, datetime, files):
      zip_filename = "pagos_corporativos_%s.zip" % datetime.strftime("%Y%m%d%H%M%S")
      bitIO = BytesIO()
      zip_file = zipfile.ZipFile(bitIO, "w", zipfile.ZIP_DEFLATED)
      for file_name, file_value in files:
         zip_file.writestr(file_name, file_value)
      zip_file.close()
      return [zip_filename, bitIO.getvalue()]

   @http.route('/download_file', type='http', auth="public")        
   def download_file(self):
      #Validamos los datos
      if request.params.get('ids') == None:
         _logger.error('No se obtuvierons ids por parametro')
         return

      payments_request_ids = request.params.get('ids').split(',')

      local_payments_request_cl = self.get_payments_request_by_ids(payments_request_ids, 'CL', 'CLP')
      localpayments_request_mx = self.get_payments_request_by_ids(payments_request_ids, 'MX', 'MXN')
      international_payments_request_mx = self.get_payments_request_by_ids(payments_request_ids, 'MX', 'USD')
      datetime_now = datetime.now()
      compress_files = []

      _logger.info('local_payments_request_cl')
      _logger.info(local_payments_request_cl)
      _logger.info('localpayments_request_mx')
      _logger.info(localpayments_request_mx)
      _logger.info('international_payments_request_mx')
      _logger.info(international_payments_request_mx)

      if len(local_payments_request_cl) > 0:
         file_santander_cl_name, xls_santander_cl_value = self.generate_xls_santander_cl_value(datetime_now, local_payments_request_cl)
         compress_files.append([file_santander_cl_name, xls_santander_cl_value])

      if len(localpayments_request_mx) > 0:
         local_file_ve_por_mas_mx_name, local_xls_ve_por_mas_mx_value = self.generate_xls_ve_por_mas_mx_value(datetime_now, localpayments_request_mx, False)
         compress_files.append([local_file_ve_por_mas_mx_name, local_xls_ve_por_mas_mx_value])

      if len(international_payments_request_mx) > 0:
         international_file_ve_por_mas_mx_name, international_xls_ve_por_mas_mx_value = self.generate_xls_ve_por_mas_mx_value(datetime_now, international_payments_request_mx, True)
         compress_files.append([international_file_ve_por_mas_mx_name, international_xls_ve_por_mas_mx_value])
      
      if len(compress_files) == 0:
         _logger.error('No hay archivos para procesar')
         return
      
      zip_filename, zip_value = self.generate_zip_value(datetime_now, compress_files)

      return request.make_response(zip_value,
                                     headers=[('Content-Type', 'application/x-zip-compressed'),
                                              ('Content-Disposition', content_disposition(zip_filename))])


   

