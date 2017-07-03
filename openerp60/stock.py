# -*- encoding: utf-8 -*-
import openerp_link as lnk
import time


def audit_tcv_stock_changes(context):
    date_start = context.get('date_start')
    date_end = context.get('date_end')
    res = {
        'name': u'Ajustes a lotes de inventario pendientes',
        'group': 'stock',
        'data': [],
        'detail': u'Se deben aprobar los albaranes correspondientes. '
                  'Primero la salida y luego la entrada.',
        'start': time.time(),
        }
    changes_ids = lnk.execute(
        'tcv.stock.changes', 'search',
        [('date', '>=', date_start), ('date', '<=', date_end)])
    changes = lnk.execute(
        'tcv.stock.changes', 'read', changes_ids,
        ('ref', 'date', 'state', 'picking_out_id', 'picking_in_id'))
    for c in changes:
        data = {}
        if not res['data']:
            res['data'].append((
                'Ajuste', 'Fecha', 'Estado', 'Alb. salida', 'Alb. Entrada'))
        if c['state'] not in ('done', 'cancel'):
            data['state'] = c['state']
        if c['picking_out_id']:
            picking = lnk.execute(
                'stock.picking', 'read', c['picking_out_id'][0],
                ('name', 'state'))
            if picking['state'] not in ('done', 'cancel'):
                data['picking_out_id'] = '%s: %s' % (picking['name'],
                                                     picking['state'])
        if c['picking_in_id']:
            picking = lnk.execute(
                'stock.picking', 'read', c['picking_in_id'][0],
                ('name', 'state'))
            if picking['state'] not in ('done', 'cancel'):
                data['picking_in_id'] = '%s: %s' % (picking['name'],
                                                    picking['state'])
        if data:
            res['data'].append((
                c['ref'], c['date'], c['state'],
                data['picking_out_id'], data['picking_in_id']))
    if len(res['data']) == 1:
        res['data'] = []
    return res


def audit_tcv_bunble_status(context):
    #~ date_start = context.get('date_start')
    #~ date_end = context.get('date_end')
    res = {
        'name': u'Estatus de bundles de exportación',
        'group': 'stock',
        'data': [],
        'detail': u'Comprueba la disponibilidad real de los bundles de ' +
                  u'exportación y el peso. Deben ajustarse los campos ' +
                  u'según corresponda. Almacen -> Trazabilidad -> Bulto. ' +
                  u'(No se usa límite de fechas)',
        'start': time.time(),
        }
    bundles_ids = lnk.execute(
        'tcv.bundle', 'search', [])
    bundles = lnk.execute(
        'tcv.bundle', 'read', bundles_ids,
        ('name', 'line_ids', 'weight_net', 'location_id', 'product_id',
         'reserved'))
    parent_ids = lnk.execute(
        'stock.location', 'search', [('name', '=', u'Exportación')])
    export_locations = lnk.execute(
        'stock.location', 'search', [('location_id', 'in', parent_ids)])
    for b in bundles:
        #~ data = {}
        obs = []
        if not b['weight_net'] and not b['reserved']:
            obs.append('Peso 0')
        if not b['location_id'] and not b['reserved']:
            obs.append(u'Bundle sin Ubicación')
        tracking_id = lnk.execute(
            'stock.tracking', 'search', [('name', '=', b['name'])])
        if b['reserved']:  # Reservados
            if not tracking_id:
                obs.append(u'Bundle reservado sin Paquete asociado')
        else:  # Disponibles
            if b['location_id'] and \
                    b['location_id'][0] not in export_locations:
                obs.append(u'Ubicación incorrecta para exportación')
            if tracking_id:
                obs.append(u'Bundle disponible con Paquete asociado')
            location_errors = []
            #~ Validar ubicacion de lotes = ubic. bundle (Solo disponibles)
            for l in b['line_ids']:
                if b['location_id']:
                    line = lnk.execute(
                        'tcv.bundle.lines', 'read', l, ['prod_lot_id'])
                    lot_location = lnk.execute(
                        'stock.production.lot', 'get_actual_lot_location',
                        line['prod_lot_id'][0])
                    if not lot_location or \
                            lot_location[0] != b['location_id'][0]:
                        location_errors.append(
                            line['prod_lot_id'][1].split(' ')[0])
            if location_errors:
                obs.append(u'Ubicación distinta bundle y lote: %s' %
                           ', '.join(location_errors))
        if not b['line_ids']:
            obs.append('Bundle sin lotes')
        if obs:
            if not res['data']:
                res['data'].append((
                    'Bundle', 'Producto', u'Ubicación', 'Peso',
                    u'Observaciones'))
            res['data'].append((
                b['name'],
                b['product_id'][1],
                b['location_id'] and b['location_id'][1] or '',
                b['weight_net'],
                u', '.join(obs)))
    return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
