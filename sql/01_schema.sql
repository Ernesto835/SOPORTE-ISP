CREATE DATABASE IF NOT EXISTS isp_soporte;
USE isp_soporte;

CREATE TABLE IF NOT EXISTS clientes (
    cliente_id UUID DEFAULT gen_random_uuid(),
    nombre STRING(100) NOT NULL,
    correo STRING(100) NOT NULL UNIQUE,
    telefono STRING(20),
    plan_contratado STRING(50) NOT NULL,
    estado STRING(20) DEFAULT 'activo',
    creado_at TIMESTAMP DEFAULT now(),
    CONSTRAINT pk_clientes PRIMARY KEY (cliente_id),
    CONSTRAINT chk_estado_cliente CHECK (estado IN ('activo', 'suspendido', 'retirado'))
);

CREATE TABLE IF NOT EXISTS tickets (
    ticket_id UUID DEFAULT gen_random_uuid(),
    region STRING(20) NOT NULL,
    cliente_id UUID NOT NULL,
    asunto STRING(150) NOT NULL,
    descripcion TEXT,
    prioridad STRING(20) NOT NULL DEFAULT 'media',
    estado STRING(20) NOT NULL DEFAULT 'abierto',
    creado_at TIMESTAMP DEFAULT now(),
    cerrado_at TIMESTAMP,
    CONSTRAINT pk_tickets PRIMARY KEY (region, ticket_id),
    CONSTRAINT fk_tickets_clientes FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id) ON DELETE CASCADE,
    CONSTRAINT chk_region CHECK (region IN ('Norte', 'Centro', 'Sur')),
    CONSTRAINT chk_prioridad CHECK (prioridad IN ('baja', 'media', 'alta', 'critica')),
    CONSTRAINT chk_estado_ticket CHECK (estado IN ('abierto', 'en_proceso', 'resuelto', 'cerrado'))
);

CREATE TABLE IF NOT EXISTS historial_estados (
    historial_id UUID DEFAULT gen_random_uuid(),
    region STRING(20) NOT NULL,
    ticket_id UUID NOT NULL,
    estado_anterior STRING(20),
    estado_nuevo STRING(20) NOT NULL,
    comentario TEXT,
    tecnico_asignado STRING(100),
    actualizado_at TIMESTAMP DEFAULT now(),
    CONSTRAINT pk_historial PRIMARY KEY (region, historial_id),
    CONSTRAINT fk_historial_tickets FOREIGN KEY (region, ticket_id) REFERENCES tickets(region, ticket_id) ON DELETE CASCADE
);
