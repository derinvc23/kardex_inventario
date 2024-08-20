# -*- coding: utf-8 -*-
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx

import datetime
import calendar


class KardexXlsx(ReportXlsx):

    def get_lines(self, location, product):
        lines = []
        cr = self.env.cr
        cr.execute("""
        SELECT MIN(foo.id)                                                                             as id,
               to_char(foo.date, 'DD/MM/YYYY')                                                         as fecha,
               move_id,
               coalesce(sp.name, sm.name)                                                              as picking,
               CASE
                   WHEN spt.code = 'incoming' THEN
                       'COMPRA'
                   WHEN spt.code = 'outgoing' THEN
                       'VENTA'
                   WHEN spt.code = 'internal' THEN
                       'TRANSFERENCIA INTERNA'
                   ELSE
                       'AJUSTE INVENTARIO'
                   END                                                                                 as descripcion,
               foo.location_id,
               foo.company_id,
               foo.product_id,
               foo.product_categ_id,
               foo.product_template_id,
               SUM(foo.quantity)                                                                       as quantity,
        
               COALESCE(SUM(foo.price_unit_on_quant * foo.quantity) / NULLIF(SUM(foo.quantity), 0), 0) as price_unit_on_quant,
               foo.source,
               string_agg(DISTINCT foo.serial_number, ', ' ORDER BY foo.serial_number)                 AS serial_number,
               foo.date::DATE as fecha2
        FROM ((SELECT stock_move.id             AS id,
                      stock_move.id             AS move_id,
                      stock_move.picking_id     AS picking_id,
                      dest_location.id          AS location_id,
                      dest_location.company_id  AS company_id,
                      stock_move.product_id     AS product_id,
                      product_template.id       AS product_template_id,
                      product_template.categ_id AS product_categ_id,
                      quant.qty                 AS quantity,
                      stock_move.date           AS date,
                      quant.cost                as price_unit_on_quant,
                      stock_move.origin         AS source,
                      stock_production_lot.name AS serial_number
               FROM stock_quant as quant
                        JOIN
                    stock_quant_move_rel ON stock_quant_move_rel.quant_id = quant.id
                        JOIN
                    stock_move ON stock_move.id = stock_quant_move_rel.move_id
                        LEFT JOIN
                    stock_production_lot ON stock_production_lot.id = quant.lot_id
                        JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                        JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                        JOIN
                    product_product ON product_product.id = stock_move.product_id
                        JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
               WHERE quant.qty > 0
                 AND stock_move.state = 'done'
                 AND dest_location.usage in ('internal', 'transit')
                 AND (
                       not (source_location.company_id is null and dest_location.company_id is null) or
                       source_location.company_id != dest_location.company_id or
                       source_location.usage not in ('internal', 'transit')))
              UNION ALL
              (SELECT (-1) * stock_move.id       AS id,
                      stock_move.id              AS move_id,
                      stock_move.picking_id      AS picking_id,
                      source_location.id         AS location_id,
                      source_location.company_id AS company_id,
                      stock_move.product_id      AS product_id,
                      product_template.id        AS product_template_id,
                      product_template.categ_id  AS product_categ_id,
                      - quant.qty                AS quantity,
                      stock_move.date            AS date,
                      quant.cost                 as price_unit_on_quant,
                      stock_move.origin          AS source,
                      stock_production_lot.name  AS serial_number
               FROM stock_quant as quant
                        JOIN
                    stock_quant_move_rel ON stock_quant_move_rel.quant_id = quant.id
                        JOIN
                    stock_move ON stock_move.id = stock_quant_move_rel.move_id
                        LEFT JOIN
                    stock_production_lot ON stock_production_lot.id = quant.lot_id
                        JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                        JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                        JOIN
                    product_product ON product_product.id = stock_move.product_id
                        JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
               WHERE quant.qty > 0
                 AND stock_move.state = 'done'
                 AND source_location.usage in ('internal', 'transit')
                 AND (
                       not (dest_location.company_id is null and source_location.company_id is null) or
                       dest_location.company_id != source_location.company_id or
                       dest_location.usage not in ('internal', 'transit'))))
                 AS foo
                 left join stock_picking sp on sp.id = foo.picking_id
                 left join stock_move sm on sm.id = foo.move_id
                 left join stock_picking_type spt on spt.id = sm.picking_type_id
        where foo.product_id = %s
          and foo.location_id = %s
        GROUP BY foo.move_id,
                 sp.name,
                 sm.name,
                 spt.code,
                 foo.location_id,
                 foo.company_id,
                 foo.product_id,
                 foo.product_categ_id,
                 foo.date,
                 foo.source,
                 foo.product_template_id
        order by foo.date
        """, (product, location))
        res = cr.fetchall()
        valor = 1
        for ln in res:
            vals = {
                'a': ln[1],
                'b': ln[2],
                'c': ln[3],
                'd': ln[4],
                'e': ln[10],
                'f': ln[10] * ln[11],
                'h': ln[14]
            }
            valor += 1
            lines.append(vals)
        return lines

    def generate_xlsx_report(self, workbook, data, lines):
        wizard = data
        sheet = workbook.add_worksheet('Libro de Ventas Estandar')
        format1 = workbook.add_format(
            {'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter',
             'bold': True})
        format11 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True,
             'bold': False})
        format10 = workbook.add_format(
            {'font_size': 10, 'align': 'right', 'right': True, 'left': True, 'bottom': False, 'top': False,
             'bold': False})
        format21 = workbook.add_format(
            {'font_size': 9, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True,
             'bold': False})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'align': 'right', 'font_size': 10})
        format3_b = workbook.add_format({'bottom': True, 'top': True, 'align': 'right', 'font_size': 10, 'bold': True})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        font_size_number_8 = workbook.add_format(
            {'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8, 'num_format': '#,##0.00'})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                        'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        format21.set_align('center')
        format21.set_align('vcenter')
        sheet.set_column('A:J', 17)
        # sheet.set_row(7, 60)
        company = self.env['res.company'].browse(data['form']['company_id'])
        sheet.merge_range('A1:B1', company.name, format10)
        sheet.merge_range('A2:B2', 'OFICINA CENTRAL', format10)
        sheet.merge_range('D3:F3', 'KARDEX DE PRODUCTO', format11)
        sheet.merge_range('D4:F4', 'DEL:' + str(data['form']['date_from']) + ' AL ' + str(data['form']['date_to']),
                          format11)
        sheet.merge_range('D5:F5', 'EXPRESADO EN BOLIVIANOS', format11)
        row = 7
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        for location in data['form']['location_ids']:
            warehouse = self.env['stock.warehouse'].search([('lot_stock_id', '=', location)])
            loc = self.env['stock.location'].browse(location)
            sheet.write(row, 0, u'SUCURSAL', format3_b)
            if warehouse:
                sheet.write(row, 1, warehouse[0].name, format3)
            else:
                sheet.write(row, 1, loc.complete_name, format3)
            row += 1
            for product in data['form']['product_ids']:
                prod = self.env['product.product'].browse(product)
                sheet.write(row, 0, u'PRODUCTO', format21)
                sheet.write(row, 1, u'CÓDIGO DE BARRAS', format21)
                sheet.write(row, 2, u'CÖDIGO INTERNO', format21)
                sheet.write(row, 3, u'FECHA', format21)
                sheet.write(row, 4, u'NRO. TRANSACCIÓN', format21)
                sheet.write(row, 5, u'SEC-TRANSACCIÓN', format21)
                sheet.write(row, 6, u'DESCRIPCIÓN', format21)
                sheet.write(row, 7, u'CANTIDAD', format21)
                sheet.write(row, 8, u'IMPORTE', format21)
                sheet.write(row, 9, u'CANTIDAD A FECHA', format21)
                if self.env.user.has_group('stock_account.group_inventory_valuation'):
                    sheet.write(row, 10, u'IMPORTE A FECHA', format21)
                    sheet.write(row, 11, u'COSTO PROMEDIO', format21)
                # row += 1
                # sheet.write(row, 0, u'PRODUCTO', format3_b)
                # sheet.write(row, 1, prod.name, format3)
                # sheet.write(row, 3, u'CÓDIGO DE BARRAS', format3_b)
                # sheet.write(row, 4, prod.barcode, format3)
                # sheet.write(row, 6, u'CÓDIGO INTERNO', format3_b)
                # sheet.write(row, 7, prod.default_code, format3)
                get_line = self.get_lines(location, product)
                row += 1
                cant_fecha = 0
                monto_fecha = 0
                sheet.write(row, 6, u'SALDO INICIAL', format3_b)
                sheet.write(row, 7, cant_fecha, font_size_number_8)
                sheet.write(row, 8, monto_fecha, font_size_number_8)
                tot_a = 0
                tot_b = 0
                for li in get_line:
                    if li['h'] >= date_from and li['h'] <= date_to:
                        row += 1
                        cant_fecha += li['e']
                        monto_fecha += li['f']
                        sheet.write(row, 0, prod.name, font_size_8)
                        sheet.write(row, 1, prod.barcode, font_size_8)
                        sheet.write(row, 2, prod.default_code, font_size_8)
                        sheet.write(row, 3, li['a'], font_size_8)
                        sheet.write(row, 4, li['b'], font_size_8)
                        sheet.write(row, 5, li['c'], font_size_8)
                        sheet.write(row, 6, li['d'], font_size_8)
                        sheet.write(row, 7, li['e'], font_size_number_8)
                        sheet.write(row, 8, li['f'], font_size_number_8)
                        sheet.write(row, 9, cant_fecha or 0, font_size_number_8)
                        if self.env.user.has_group('stock_account.group_inventory_valuation'):
                            sheet.write(row, 10, monto_fecha or 0, font_size_number_8)
                            if cant_fecha > 0:
                                sheet.write(row, 11, monto_fecha / cant_fecha, font_size_number_8)
                            else:
                                sheet.write(row, 11, 0, font_size_number_8)

                        tot_a += li['e']
                        tot_b += li['f']
                    elif li['h'] < date_from:
                        cant_fecha += li['e']
                        monto_fecha += li['f']
                        sheet.write(row, 6, u'SALDO INICIAL', format3_b)
                        sheet.write(row, 7, cant_fecha, font_size_number_8)
                        sheet.write(row, 8, monto_fecha, font_size_number_8)
                row += 1
                sheet.write(row, 6, u'TOTAL', format3_b)
                sheet.write_number(row, 7, tot_a, font_size_number_8)
                sheet.write_number(row, 8, tot_b, font_size_number_8)
                row += 2


KardexXlsx('report.kardex_inventario.kardex_xlsx.xlsx',
           'kardex.inventario.wizard')
