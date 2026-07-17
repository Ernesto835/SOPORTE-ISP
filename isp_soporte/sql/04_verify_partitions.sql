-- =============================================================================
-- VERIFICACIÓN DE PARTICIONAMIENTO - SHOW RANGES
-- REQUISITO: Verificar la fragmentación aplicada con SHOW RANGES
-- =============================================================================
USE isp_soporte;

-- Verificar rangos de la tabla 'tickets' particionada por LIST (region)
SHOW RANGES FROM TABLE tickets;

-- Verificar rangos de la tabla 'historial_estados' particionada por LIST (region)
SHOW RANGES FROM TABLE historial_estados;

-- Verificar estructura de particiones declaradas (sintaxis CockroachDB)
SHOW PARTITIONS FROM TABLE tickets;

SHOW PARTITIONS FROM TABLE historial_estados;
