# ==============================================================================
# SCRIPT DE GENERACIÓN Y POBLAMIENTO MASIVO DE DATOS - ISP SOPORTE
# REQUISITO: Generar e insertar >= 10,000 registros en el clúster
# ==============================================================================

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
import random

# Inicialización de Faker en español
fake = Faker('es_ES')

# Configuración de conexiones
CLUSTER_URI = "postgresql://root@localhost:26257/isp_soporte?sslmode=disable"
SINGLE_URI = "postgresql://root@localhost:26260/isp_soporte?sslmode=disable"

# Constantes del negocio ISP
PLANES = ['Internet Fibra 100 Mbps', 'Internet Fibra 300 Mbps', 'Internet Fibra 600 Mbps', 'Plan Gamer 1 Gbps']
ESTADOS_CLIENTE = ['activo', 'suspendido', 'retirado']
REGIONES = ['Norte', 'Centro', 'Sur']
PRIORIDADES = ['baja', 'media', 'alta', 'critica']
ESTADOS_TICKET = ['abierto', 'en_proceso', 'resuelto', 'cerrado']
ASUNTOS_TICKET = [
    'Sin señal de internet', 'Lentitud en la navegación', 'Fallas en la red Wi-Fi',
    'Cambio de clave del Router', 'Problemas con streaming', 'Corte de cable de fibra',
    'Solicitud de IP fija', 'Inconsistencia en la facturación', 'Problemas de latencia en juegos'
]


def conectar_db(uri=None):
    """Establece conexión con una instancia de CockroachDB"""
    target = uri or CLUSTER_URI
    try:
        conn = psycopg2.connect(target)
        conn.autocommit = False  # Manejo manual de transacciones
        return conn
    except Exception as e:
        print(f"[-] Error al conectar con CockroachDB ({target}): {e}")
        return None


def poblar_datos(uri=None, label=""):
    """Puebla datos en una instancia de CockroachDB específica"""
    target = uri or CLUSTER_URI
    tag = f" [{label}]" if label else ""
    print(f"[+] Conectando a CockroachDB{tag} ({target})...")
    conn = conectar_db(target)
    if not conn:
        print(f"[-] No se pudo conectar a {target}. Saltando esta instancia.")
        return False
    cursor = conn.cursor()

    try:
        # ----------------------------------------------------------------------
        # BLOQUE 1: Generación masiva de Clientes (2,000 registros)
        # ----------------------------------------------------------------------
        print("[+] Generando 2,000 clientes ficticios...")
        clientes = []
        for _ in range(2000):
            clientes.append((
                fake.name(),
                fake.unique.email(),
                fake.phone_number()[:20],
                random.choice(PLANES),
                random.choice(ESTADOS_CLIENTE)
            ))

        # Inserción masiva optimizada
        query_clientes = """
            INSERT INTO clientes (nombre, correo, telefono, plan_contratado, estado)
            VALUES %s RETURNING cliente_id;
        """
        execute_values(cursor, query_clientes, clientes)
        # Recuperamos los IDs de los clientes creados para asociarlos a los tickets
        conn.commit()
        
        cursor.execute("SELECT cliente_id FROM clientes;")
        clientes_ids = [row[0] for row in cursor.fetchall()]
        print(f"[+] Clientes insertados exitosamente. Total recuperados: {len(clientes_ids)}")

        # ----------------------------------------------------------------------
        # BLOQUE 2: Generación masiva de Tickets (6,000 registros)
        # ----------------------------------------------------------------------
        print("[+] Generando 6,000 tickets de soporte distribuidos por región...")
        tickets = []
        for _ in range(6000):
            estado_ticket = random.choice(ESTADOS_TICKET)
            creado = fake.date_time_this_year(before_now=True, after_now=False)
            cerrado = fake.date_time_between_dates(datetime_start=creado) if estado_ticket in ['resuelto', 'cerrado'] else None
            
            tickets.append((
                random.choice(REGIONES),      # Clave de partición
                random.choice(clientes_ids),  # FK a Clientes
                random.choice(ASUNTOS_TICKET),
                fake.paragraph(nb_sentences=3),
                random.choice(PRIORIDADES),
                estado_ticket,
                creado,
                cerrado
            ))

        query_tickets = """
            INSERT INTO tickets (region, cliente_id, asunto, descripcion, prioridad, estado, creado_at, cerrado_at)
            VALUES %s RETURNING region, ticket_id;
        """
        execute_values(cursor, query_tickets, tickets)
        conn.commit()

        # Recuperamos las llaves compuestas de los tickets para el historial
        cursor.execute("SELECT region, ticket_id, estado FROM tickets;")
        tickets_info = cursor.fetchall()
        print(f"[+] Tickets insertados exitosamente. Total recuperados: {len(tickets_info)}")

        # ----------------------------------------------------------------------
        # BLOQUE 3: Generación de Historial de Estados (4,500 registros)
        # ----------------------------------------------------------------------
        print("[+] Generando 4,500 entradas de historial de auditoría de tickets...")
        historial = []
        # Seleccionamos una muestra aleatoria de tickets para simular cambios de estado
        tickets_muestra = random.sample(tickets_info, 4500)
        
        for region, ticket_id, estado_actual in tickets_muestra:
            estado_previo = 'abierto' if estado_actual != 'abierto' else None
            historial.append((
                region,              # Clave de partición
                ticket_id,           # FK compuesta (parte 1)
                estado_previo,
                estado_actual,
                fake.sentence(nb_words=10),
                fake.name(),
                fake.date_time_this_month()
            ))

        query_historial = """
            INSERT INTO historial_estados (region, ticket_id, estado_anterior, estado_nuevo, comentario, tecnico_asignado, actualizado_at)
            VALUES %s;
        """
        execute_values(cursor, query_historial, historial)
        conn.commit()
        print("[+] Historial de estados insertado exitosamente.")

        # ----------------------------------------------------------------------
        # CONFIRMACIÓN TOTAL DE DATOS INSERTADOS
        # ----------------------------------------------------------------------
        cursor.execute("SELECT COUNT(*) FROM clientes;")
        total_clientes = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets;")
        total_tickets = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM historial_estados;")
        total_historial = cursor.fetchone()[0]

        total_registros = total_clientes + total_tickets + total_historial
        print("\n" + "="*50)
        print(" RESUMEN DE POBLAMIENTO MASIVO (ISP SOPORTE)")
        print("="*50)
        print(f" - Clientes insertados:          {total_clientes}")
        print(f" - Tickets creados:              {total_tickets}")
        print(f" - Historial de estados creado:  {total_historial}")
        print(f" - TOTAL REGISTROS EN LA BDD:    {total_registros}")
        print("="*50)
        print(f"[+] ¡Carga de datos masiva completada con éxito{tag}!")
        return True

    except Exception as e:
        conn.rollback()
        print(f"[-] Ocurrió un error durante la inserción{tag}: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def verificar_tablas_existen(uri):
    """Verifica si las tablas del esquema ya existen en la instancia"""
    conn = conectar_db(uri)
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_schema = 'isp_soporte'
              AND table_name IN ('clientes', 'tickets', 'historial_estados');
        """)
        count = cursor.fetchone()[0]
        return count == 3
    except Exception:
        return False
    finally:
        conn.close()


def crear_esquema(uri):
    """Crea el esquema completo (tablas + particiones) en una instancia CockroachDB"""
    conn = conectar_db(uri)
    if not conn:
        return False
    try:
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute("CREATE DATABASE IF NOT EXISTS isp_soporte;")
        cursor.execute("USE isp_soporte;")

        cursor.execute("""
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
        """)

        cursor.execute("""
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
        """)

        cursor.execute("""
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
        """)

        # Las particiones requieren licencia CockroachDB Enterprise (CCL).
        # Se aplican en un try/except separado: si fallan, las tablas siguen
        # siendo válidas y los datos se pueden insertar igualmente.
        try:
            cursor.execute("""
                ALTER TABLE tickets PARTITION BY LIST (region) (
                    PARTITION p_norte VALUES IN ('Norte'),
                    PARTITION p_centro VALUES IN ('Centro'),
                    PARTITION p_sur VALUES IN ('Sur')
                );
            """)
            cursor.execute("""
                ALTER TABLE historial_estados PARTITION BY LIST (region) (
                    PARTITION p_norte VALUES IN ('Norte'),
                    PARTITION p_centro VALUES IN ('Centro'),
                    PARTITION p_sur VALUES IN ('Sur')
                );
            """)
            print("[+] Esquema creado exitosamente (3 tablas + particiones).")
        except Exception as e:
            print(f"[!] Particionamiento no aplicado (requiere licencia Enterprise): {e}")
            print("[+] Esquema creado exitosamente (3 tablas, sin particiones CCL).")

        return True
    except Exception as e:
        print(f"[-] Error al crear esquema: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    # FASE 1: Poblar el clúster (nodo principal)
    poblar_datos(uri=CLUSTER_URI, label="CLÚSTER")

    # FASE 2: Poblar el nodo único para benchmark comparativo
    print("\n" + "-"*50)
    print("[+] Verificando nodo único para benchmark...")
    if verificar_tablas_existen(SINGLE_URI):
        print("[+] Nodo único detectado con esquema. Poblando datos...")
        poblar_datos(uri=SINGLE_URI, label="NODO ÚNICO")
    else:
        print("[+] Nodo único sin esquema. Creando esquema automáticamente...")
        if crear_esquema(SINGLE_URI):
            print("[+] Esquema creado. Poblando datos en nodo único...")
            poblar_datos(uri=SINGLE_URI, label="NODO ÚNICO")
        else:
            print("[-] No se pudo crear el esquema en el nodo único. Saltando.")