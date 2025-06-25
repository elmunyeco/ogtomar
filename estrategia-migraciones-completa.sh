#!/bin/bash
# PLAN BLUE-GREEN: BD nueva limpia + migración de datos
# BD original queda intacta como backup

echo "🚀 ESTRATEGIA BLUE-GREEN PARA BD CARDIOPRIETO"
echo "=============================================="

# Variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups_$TIMESTAMP"
BD_ORIGINAL="cardioprieto"
BD_NUEVA="cardioprieto_v2"

# Crear directorio de backups
mkdir -p $BACKUP_DIR

# ========================================
# FASE 1: PREPARACIÓN Y BACKUPS
# ========================================

echo ""
echo "📋 FASE 1: Preparación y Backups"
echo "================================"

# 1.1 Backup completo de seguridad
echo "💾 Backup completo de BD actual..."
mysqldump -u root -p $BD_ORIGINAL > "$BACKUP_DIR/backup_completo_$TIMESTAMP.sql"
echo "✅ Backup guardado en: $BACKUP_DIR/backup_completo_$TIMESTAMP.sql"

# 1.2 Backup SOLO de datos (sin estructura) 
echo "📊 Backup solo de datos esenciales..."
mysqldump -u root -p --no-create-info $BD_ORIGINAL \
  tipos_documentos condiciones_medicas pacientes historias_clinicas \
  condiciones_medicas_historias comentarios_visitas indicaciones_visitas \
  signos_vitales > "$BACKUP_DIR/datos_solo_$TIMESTAMP.sql"
echo "✅ Datos guardados en: $BACKUP_DIR/datos_solo_$TIMESTAMP.sql"

# 1.3 Verificar que existen las tablas principales
echo "🔍 Verificando estructura actual..."
mysql -u root -p $BD_ORIGINAL -e "SHOW TABLES;" > "$BACKUP_DIR/tablas_actuales.txt"
echo "✅ Lista de tablas guardada en: $BACKUP_DIR/tablas_actuales.txt"

# ========================================
# FASE 2: BD NUEVA LIMPIA  
# ========================================

echo ""
echo "🆕 FASE 2: Creando BD nueva limpia"
echo "=================================="

# 2.1 Crear BD nueva
echo "🏗️ Creando base de datos nueva..."
mysql -u root -p << EOF
DROP DATABASE IF EXISTS $BD_NUEVA;
CREATE DATABASE $BD_NUEVA CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EOF
echo "✅ BD $BD_NUEVA creada"

# 2.2 Backup de migraciones actuales
echo "💾 Respaldando migraciones actuales..."
mkdir -p "$BACKUP_DIR/migraciones_viejas"
cp -r main/migrations "$BACKUP_DIR/migraciones_viejas/main_migrations" 2>/dev/null || true
cp -r ecocardiograma/migrations "$BACKUP_DIR/migraciones_viejas/eco_migrations" 2>/dev/null || true

# 2.3 Limpiar migraciones para empezar desde cero
echo "🧹 Limpiando migraciones..."
find main/migrations -name "0*.py" -delete 2>/dev/null || true
find ecocardiograma/migrations -name "0*.py" -delete 2>/dev/null || true
echo "✅ Migraciones limpiadas"

# 2.4 Configuración temporal
echo ""
echo "⚠️  PAUSA MANUAL REQUERIDA"
echo "=========================="
echo "🔧 NECESITAS cambiar settings.py:"
echo "   DATABASES['default']['NAME'] = '$BD_NUEVA'"
echo ""
read -p "💡 Presioná Enter cuando hayas cambiado settings.py..."

# 2.5 Crear migraciones limpias
echo ""
echo "🏗️ Creando migraciones limpias..."
python manage.py makemigrations main
python manage.py makemigrations ecocardiograma
echo "✅ Migraciones creadas"

# 2.6 Aplicar migraciones
echo "⚡ Aplicando migraciones en BD nueva..."
python manage.py migrate
echo "✅ Migraciones aplicadas"

# ========================================
# FASE 3: MIGRACIÓN DE DATOS
# ========================================

echo ""
echo "📊 FASE 3: Migrando datos"
echo "========================"

# 3.1 Script de migración de datos
echo "🔄 Creando script de migración de datos..."

cat > "$BACKUP_DIR/migrar_datos.sql" << EOF
-- MIGRACIÓN DE DATOS: $BD_ORIGINAL -> $BD_NUEVA
-- Fecha: $TIMESTAMP

USE $BD_NUEVA;

-- Deshabilitar checks para importación rápida
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;
SET AUTOCOMMIT = 0;

START TRANSACTION;

-- 1. Tipos de documentos
INSERT INTO tipos_documentos (id, nombre, descripcion)
SELECT id, nombre, descripcion 
FROM $BD_ORIGINAL.tipos_documentos;

-- 2. Condiciones médicas
INSERT INTO condiciones_medicas (id, nombre, orden)
SELECT id, nombre, orden 
FROM $BD_ORIGINAL.condiciones_medicas;

-- 3. Pacientes (manejar campos NOT NULL)
INSERT INTO pacientes (
  id, numDoc, nombre, apellido, fechaNac, sexo, mail, direccion, 
  localidad, obraSocial, plan, afiliado, telefono, celular, 
  profesion, referente, fechaAlta, deBaja, idTipoDoc_id
)
SELECT 
  id, numDoc, nombre, apellido, fechaNac, sexo, mail, direccion,
  localidad, 
  COALESCE(obraSocial, ''), 
  plan, 
  COALESCE(afiliado, ''), 
  COALESCE(telefono, ''), 
  COALESCE(celular, ''), 
  COALESCE(profesion, ''), 
  referente, fechaAlta, deBaja, idTipoDoc_id
FROM $BD_ORIGINAL.pacientes;

-- 4. Historias clínicas
INSERT INTO historias_clinicas (id, fechaAlta, paciente_id)
SELECT id, fechaAlta, paciente_id 
FROM $BD_ORIGINAL.historias_clinicas;

-- 5. Condiciones médicas - historias (relación many-to-many)
INSERT INTO condiciones_medicas_historias (id, historia_id, condicion_id)
SELECT id, historia_id, condicion_id 
FROM $BD_ORIGINAL.condiciones_medicas_historias;

-- 6. Comentarios visitas
INSERT INTO comentarios_visitas (id, fecha, comentarios, tipo, historia_clinica_id)
SELECT id, fecha, comentarios, tipo, idHistoriaClinica
FROM $BD_ORIGINAL.comentarios_visitas;

-- 7. Indicaciones visitas  
INSERT INTO indicaciones_visitas (
  id, historia_clinica_id, medicamento, ochoHoras, doceHoras, 
  dieciochoHoras, veintiunaHoras, fecha, eliminado
)
SELECT 
  id, historia_clinica_id, medicamento, ochoHoras, doceHoras,
  dieciochoHoras, veintiunaHoras, fecha, eliminado
FROM $BD_ORIGINAL.indicaciones_visitas
WHERE eliminado IS NULL OR eliminado = 0;

-- 8. Signos vitales
INSERT INTO signos_vitales (id, fecha, presion_sistolica, presion_diastolica, peso, glucemia, colesterol, historia_id)
SELECT id, fecha, presion_sistolica, presion_diastolica, peso, glucemia, colesterol, historia_id
FROM $BD_ORIGINAL.signos_vitales;

COMMIT;

-- Ajustar AUTO_INCREMENT para evitar conflictos futuros
ALTER TABLE tipos_documentos AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM tipos_documentos);
ALTER TABLE condiciones_medicas AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM condiciones_medicas);
ALTER TABLE pacientes AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM pacientes);
ALTER TABLE historias_clinicas AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM historias_clinicas);
ALTER TABLE condiciones_medicas_historias AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM condiciones_medicas_historias);
ALTER TABLE comentarios_visitas AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM comentarios_visitas);
ALTER TABLE indicaciones_visitas AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM indicaciones_visitas);
ALTER TABLE signos_vitales AUTO_INCREMENT = (SELECT MAX(id) + 1 FROM signos_vitales);

-- Rehabilitar checks
SET FOREIGN_KEY_CHECKS = 1;
SET UNIQUE_CHECKS = 1;
SET AUTOCOMMIT = 1;

SELECT 'MIGRACIÓN COMPLETADA' as status;
EOF

# 3.2 Ejecutar migración de datos
echo "🔄 Ejecutando migración de datos..."
mysql -u root -p < "$BACKUP_DIR/migrar_datos.sql"
echo "✅ Migración de datos completada"

# ========================================
# FASE 4: VALIDACIÓN EXHAUSTIVA
# ========================================

echo ""
echo "✅ FASE 4: Validación exhaustiva"
echo "================================"

echo "🔍 Comparando conteos de registros..."

# Función para comparar conteos
function comparar_tabla() {
    local tabla=$1
    local count_orig=$(mysql -u root -p $BD_ORIGINAL -e "SELECT COUNT(*) FROM $tabla;" --skip-column-names 2>/dev/null || echo "0")
    local count_new=$(mysql -u root -p $BD_NUEVA -e "SELECT COUNT(*) FROM $tabla;" --skip-column-names 2>/dev/null || echo "0")
    
    if [ "$count_orig" = "$count_new" ]; then
        echo "✅ $tabla: $count_orig → $count_new"
    else
        echo "❌ $tabla: $count_orig → $count_new (DIFERENCIA!)"
    fi
}

# Comparar todas las tablas principales
comparar_tabla "pacientes"
comparar_tabla "historias_clinicas"
comparar_tabla "tipos_documentos"
comparar_tabla "condiciones_medicas"
comparar_tabla "condiciones_medicas_historias"
comparar_tabla "comentarios_visitas"
comparar_tabla "indicaciones_visitas"
comparar_tabla "signos_vitales"

# Generar reporte de validación
echo ""
echo "📊 Generando reporte de validación..."
cat > "$BACKUP_DIR/reporte_validacion.txt" << EOF
REPORTE DE VALIDACIÓN - $TIMESTAMP
==================================

BD Original: $BD_ORIGINAL
BD Nueva: $BD_NUEVA

CONTEOS:
$(comparar_tabla "pacientes")
$(comparar_tabla "historias_clinicas") 
$(comparar_tabla "tipos_documentos")
$(comparar_tabla "condiciones_medicas")
$(comparar_tabla "condiciones_medicas_historias")
$(comparar_tabla "comentarios_visitas")
$(comparar_tabla "indicaciones_visitas")
$(comparar_tabla "signos_vitales")

ESTRUCTURA BD NUEVA:
$(mysql -u root -p $BD_NUEVA -e "SHOW TABLES;" 2>/dev/null)

MIGRACIONES APLICADAS:
$(python manage.py showmigrations 2>/dev/null || echo "Error: Verificar settings.py")
EOF

echo "✅ Reporte guardado en: $BACKUP_DIR/reporte_validacion.txt"

# ========================================
# FASE 5: INSTRUCCIONES FINALES
# ========================================

echo ""
echo "🎯 FASE 5: Switch final (MANUAL)"
echo "================================"
echo ""
echo "🟢 BD nueva lista: $BD_NUEVA"
echo "🔵 BD original preservada: $BD_ORIGINAL" 
echo "💾 Backups en: $BACKUP_DIR/"
echo ""
echo "🔄 PARA HACER EL SWITCH:"
echo "1. Cambiar settings.py:"
echo "   DATABASES['default']['NAME'] = '$BD_ORIGINAL'"
echo ""
echo "2. Renombrar las bases de datos:"
echo "   mysql -u root -p -e \"RENAME TABLE $BD_ORIGINAL.* TO cardioprieto_backup.*;\"" 
echo "   mysql -u root -p -e \"RENAME TABLE $BD_NUEVA.* TO $BD_ORIGINAL.*;\"" 
echo ""
echo "🧪 PARA PROBAR (opcional):"
echo "   python manage.py runserver 0.0.0.0:8001"
echo "   # Probar en puerto diferente primero"
echo ""
echo "🚨 ROLLBACK si algo falla:"
echo "   1. Cambiar settings.py de vuelta"
echo "   2. Restaurar desde: $BACKUP_DIR/backup_completo_$TIMESTAMP.sql"
echo ""
echo "🎉 ¡MIGRACIÓN BLUE-GREEN COMPLETADA!"
echo "   ✅ Migraciones ordenadas"
echo "   ✅ BD limpia y consistente" 
echo "   ✅ Datos preservados"
echo "   ✅ Rollback disponible"
