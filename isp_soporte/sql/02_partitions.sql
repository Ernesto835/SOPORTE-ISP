USE isp_soporte;

-- =============================================================================
-- NOTA: PARTITION BY LIST requiere licencia CockroachDB Enterprise (CCL).
-- En la versión gratuita (BSL) estas sentencias lanzarán:
--   "unimplemented: part of this query requires an enterprise license"
-- Las tablas funcionan normalmente sin particiones; CockroachDB distribuye
-- los datos automáticamente entre nodos vía su arquitectura de rangos internos.
-- =============================================================================

-- Aplicar particionamiento horizontal por Lista a la tabla principal 'tickets'
ALTER TABLE tickets PARTITION BY LIST (region) (
    PARTITION p_norte VALUES IN ('Norte'),
    PARTITION p_centro VALUES IN ('Centro'),
    PARTITION p_sur VALUES IN ('Sur')
);

-- Aplicar particionamiento horizontal por Lista a la tabla 'historial_estados'
ALTER TABLE historial_estados PARTITION BY LIST (region) (
    PARTITION p_norte VALUES IN ('Norte'),
    PARTITION p_centro VALUES IN ('Centro'),
    PARTITION p_sur VALUES IN ('Sur')
);
