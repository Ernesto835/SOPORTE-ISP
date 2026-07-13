-- ==============================================================================
-- ESQUEMA DE BASE DE DATOS ISP SOPORTE
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS isp_soporte;

USE isp_soporte;

-- Tabla: clientes
CREATE TABLE IF NOT EXISTS clientes (
  cliente_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  nombre VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL UNIQUE,
  telefono VARCHAR(20),
  estado VARCHAR(50) NOT NULL CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
  fecha_creacion TIMESTAMP DEFAULT now(),
  fecha_actualizacion TIMESTAMP DEFAULT now()
);

-- Tabla: tickets
CREATE TABLE IF NOT EXISTS tickets (
  region VARCHAR(50) NOT NULL,
  ticket_id UUID NOT NULL,
  cliente_id UUID NOT NULL,
  titulo VARCHAR(255) NOT NULL,
  descripcion TEXT,
  prioridad VARCHAR(20) NOT NULL CHECK (prioridad IN ('baja', 'media', 'alta', 'critica')),
  estado VARCHAR(50) NOT NULL CHECK (estado IN ('abierto', 'en_proceso', 'resuelto', 'cerrado')),
  fecha_creacion TIMESTAMP DEFAULT now(),
  fecha_actualizacion TIMESTAMP DEFAULT now(),
  PRIMARY KEY (region, ticket_id),
  FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id) ON DELETE CASCADE,
  CHECK (region IN ('norte', 'centro', 'sur', 'este', 'oeste'))
);

-- Tabla: historial_estados
CREATE TABLE IF NOT EXISTS historial_estados (
  region VARCHAR(50) NOT NULL,
  historial_id UUID NOT NULL,
  ticket_id UUID NOT NULL,
  estado_anterior VARCHAR(50),
  estado_nuevo VARCHAR(50) NOT NULL,
  comentario TEXT,
  fecha_cambio TIMESTAMP DEFAULT now(),
  PRIMARY KEY (region, historial_id),
  FOREIGN KEY (region, ticket_id) REFERENCES tickets(region, ticket_id) ON DELETE CASCADE
);

-- Índices para optimización
CREATE INDEX idx_tickets_cliente ON tickets(cliente_id);
CREATE INDEX idx_tickets_estado ON tickets(estado);
CREATE INDEX idx_tickets_prioridad ON tickets(prioridad);
CREATE INDEX idx_historial_ticket ON historial_estados(ticket_id);
