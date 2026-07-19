USE isp_soporte;

-- =============================================================================
-- REQUISITO: licencia CockroachDB Enterprise Free (activada en el clúster).
-- Activar con: SET CLUSTER SETTING enterprise.license = '<clave>';
-- Verificar con: SHOW PARTITIONS FROM TABLE tickets;
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
