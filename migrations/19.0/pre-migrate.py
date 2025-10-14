# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

def migrate(cr, version):
    """
    Migración pre-upgrade de Odoo 18 a 19 para módulo copier_company
    Agrega columnas que fueron añadidas después de la instalación inicial en v18
    """
    
    _logger.info("="*100)
    _logger.info("INICIANDO MIGRACIÓN COPIER_COMPANY DE v18 A v19")
    _logger.info("="*100)
    
    # Lista de campos que deben existir antes del upgrade
    campos_requeridos = [
        {
            'tabla': 'copier_whatsapp_alert',
            'columna': 'status',
            'tipo': 'VARCHAR(50)',
            'default': "'pending'",
            'update': "UPDATE copier_whatsapp_alert SET status = 'pending' WHERE status IS NULL"
        },
        {
            'tabla': 'copier_stock',
            'columna': 'name',
            'tipo': 'VARCHAR(255)',
            'default': "'New'",
            'update': """
                UPDATE copier_stock cs
                SET name = COALESCE(
                    (SELECT CONCAT(mm.name, '-', cs.id) 
                     FROM modelos_maquinas mm 
                     WHERE mm.id = cs.modelo_id),
                    CONCAT('STOCK-', cs.id)
                )
                WHERE name IS NULL OR name = 'New'
            """
        },
        {
            'tabla': 'copier_checklist_item',
            'columna': 'sequence',
            'tipo': 'INTEGER',
            'default': '10',
            'update': "UPDATE copier_checklist_item SET sequence = COALESCE(sequence, id * 10)"
        },
        {
            'tabla': 'copier_counter',
            'columna': 'fecha_facturacion',
            'tipo': 'DATE',
            'default': 'CURRENT_DATE',
            'update': """
                UPDATE copier_counter 
                SET fecha_facturacion = COALESCE(
                    fecha_facturacion,
                    fecha::date,
                    CURRENT_DATE
                )
                WHERE fecha_facturacion IS NULL
            """
        },
        {
            'tabla': 'copier_payment_mode',
            'columna': 'frecuencia_meses',
            'tipo': 'INTEGER',
            'default': '1',
            'update': "UPDATE copier_payment_mode SET frecuencia_meses = 1 WHERE frecuencia_meses IS NULL"
        }
    ]
    
    for idx, campo in enumerate(campos_requeridos, 1):
        tabla = campo['tabla']
        columna = campo['columna']
        tipo = campo['tipo']
        default = campo['default']
        update_sql = campo['update']
        
        _logger.info(f"{idx}/{len(campos_requeridos)} - Procesando {tabla}.{columna}")
        
        try:
            # Verificar si la tabla existe
            cr.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                )
            """, (tabla,))
            
            tabla_existe = cr.fetchone()[0]
            
            if not tabla_existe:
                _logger.warning(f"   ⚠ Tabla '{tabla}' no existe, saltando...")
                continue
            
            # Verificar si la columna existe
            cr.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public'
                AND table_name = %s 
                AND column_name = %s
            """, (tabla, columna))
            
            columna_existe = cr.fetchone()
            
            if not columna_existe:
                _logger.info(f"   → Agregando columna '{columna}' a '{tabla}'")
                
                # Agregar columna
                alter_sql = f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}"
                if default:
                    alter_sql += f" DEFAULT {default}"
                
                cr.execute(alter_sql)
                _logger.info(f"   ✓ Columna '{columna}' agregada")
                
                # Actualizar registros existentes
                if update_sql:
                    _logger.info(f"   → Actualizando registros existentes...")
                    cr.execute(update_sql)
                    _logger.info(f"   ✓ Registros actualizados")
            else:
                _logger.info(f"   ✓ Columna '{columna}' ya existe")
                
        except Exception as e:
            _logger.error(f"   ✗ Error procesando {tabla}.{columna}: {str(e)}")
            raise
    
    _logger.info("="*100)
    _logger.info("MIGRACIÓN COMPLETADA EXITOSAMENTE")
    _logger.info("="*100)
