-- =============================================================================
-- CINCO CONSULTAS SQL PARA PRUEBAS DE RENDIMIENTO (BENCHMARK) - ACC ISP
-- =============================================================================
USE isp_soporte;

-- -----------------------------------------------------------------------------
-- CONSULTA 1: JOIN entre Clientes y sus Tickets abiertos/en proceso
-- Propósito: Evaluar el rendimiento en cruce de datos distribuidos.
-- -----------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT c.nombre, c.plan_contratado, t.asunto, t.prioridad, t.creado_at
FROM clientes c
INNER JOIN tickets t ON c.cliente_id = t.cliente_id
WHERE t.estado IN ('abierto', 'en_proceso')
ORDER BY t.creado_at DESC
LIMIT 100;

-- -----------------------------------------------------------------------------
-- CONSULTA 2: Agrupación y conteo de tickets por Región y Prioridad (GROUP BY)
-- Propósito: Medir velocidad al escanear tablas particionadas por región.
-- -----------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT region, prioridad, COUNT(*) as total_tickets, MAX(creado_at) as ultimo_registro
FROM tickets
GROUP BY region, prioridad
ORDER BY region, total_tickets DESC;

-- -----------------------------------------------------------------------------
-- CONSULTA 3: Búsqueda puntual por clave primaria compuesta (Punto de acceso)
-- Propósito: Demostrar la eficiencia extrema del direccionamiento directo.
-- -----------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT * 
FROM tickets 
WHERE region = 'Centro' 
  AND ticket_id = '00632a1f-7dea-477e-973f-0ebbd5aa049f'; 

-- -----------------------------------------------------------------------------
-- CONSULTA 4: Consulta de rango (WHERE con filtrado de fechas y estados)
-- Propósito: Evaluar velocidad al recuperar incidentes graves del último mes.
-- -----------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT region, asunto, prioridad, estado, creado_at
FROM tickets
WHERE prioridad IN ('alta', 'critica')
  AND creado_at >= NOW() - INTERVAL '30 days'
ORDER BY creado_at ASC;

-- -----------------------------------------------------------------------------
-- CONSULTA 5: Subconsulta correlacionada compleja
-- Propósito: Listar clientes junto con la fecha de su ticket más reciente.
-- -----------------------------------------------------------------------------
EXPLAIN ANALYZE
SELECT c.cliente_id, c.nombre, c.correo,
       (SELECT MAX(t.creado_at) FROM tickets t WHERE t.cliente_id = c.cliente_id) as fecha_ultimo_ticket
FROM clientes c
WHERE c.estado = 'activo'
LIMIT 100;