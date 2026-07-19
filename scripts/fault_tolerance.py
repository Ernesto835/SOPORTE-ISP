# ==============================================================================
# SCRIPT DE PRUEBA DE TOLERANCIA A FALLOS - CLÚSTER COCKROACHDB
# REQUISITO: Detener un nodo, verificar quórum Raft, reiniciar el nodo
# ==============================================================================

import psycopg2
import subprocess
import time
import sys

CLUSTER_URI = "postgresql://root@localhost:26257/isp_soporte?sslmode=disable"
NODO_A_DETENER = "crdb-node2"
TIMEOUT_REINICIO = 60  # Máximo tiempo de espera para que el nodo vuelva a is_live=true


def ejecutar_sql(uri, query, fetch=True):
    """Ejecuta una consulta SQL y retorna resultados si aplica"""
    conn = None
    try:
        conn = psycopg2.connect(uri)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(query)
        if fetch:
            return cursor.fetchall()
        return None
    except Exception as e:
        print(f"[-] Error SQL: {e}")
        return None
    finally:
        if conn:
            conn.close()


def verificar_nodos(desc=""):
    """Verifica y muestra el estado de todos los nodos del clúster"""
    print(f"\n{'='*65}")
    if desc:
        print(f" {desc}")
        print("="*65)

    nodos = ejecutar_sql(CLUSTER_URI, """
        SELECT node_id, address, is_live
        FROM crdb_internal.gossip_nodes
        ORDER BY node_id;
    """)

    if not nodos:
        print("[-] No se pudieron consultar los nodos del clúster.")
        return 0

    print(f"{'Node ID':<12}{'Dirección':<22}{'is_live'}")
    print("-"*45)
    vivos = 0
    for node_id, address, is_live in nodos:
        estado = "ACTIVO" if is_live else "CAÍDO"
        print(f"{node_id:<12}{address:<22}{estado}")
        if is_live:
            vivos += 1

    print(f"\n[+] Nodos activos: {vivos}/3")
    return vivos


def probar_escritura():
    """Intenta insertar un registro para verificar que el clúster acepta escrituras"""
    print("\n[+] Probando escritura en el clúster...")
    resultado = ejecutar_sql(CLUSTER_URI, """
        INSERT INTO tickets (region, cliente_id, asunto, prioridad, estado)
        SELECT 'Centro', cliente_id, 'Test tolerancia a fallos', 'baja', 'abierto'
        FROM clientes LIMIT 1
        RETURNING ticket_id;
    """)
    if resultado:
        print(f"[+] Escritura exitosa. Ticket creado: {resultado[0][0]}")
        return True
    else:
        print("[-] Fallo en la escritura. El clúster no acepta datos.")
        return False


def probar_lectura():
    """Ejecuta SELECT COUNT(*) en la tabla principal (tickets) y mide el tiempo de respuesta"""
    print("[+] Probando lectura en el clúster (SELECT COUNT(*) FROM tickets)...")
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(CLUSTER_URI)
        conn.autocommit = True
        cursor = conn.cursor()

        start = time.perf_counter()
        cursor.execute("SELECT COUNT(*) FROM tickets;")
        total = cursor.fetchone()[0]
        elapsed = round((time.perf_counter() - start) * 1000, 2)

        print(f"[+] Lectura exitosa. Total tickets: {total} ({elapsed} ms)")
        return True
    except Exception as e:
        print(f"[-] Fallo en la lectura: {e}")
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def detener_nodo(nombre_nodo):
    """Detiene un contenedor Docker del clúster"""
    print(f"\n[+] DETENIENDO nodo '{nombre_nodo}'...")
    try:
        resultado = subprocess.run(
            ["docker", "stop", nombre_nodo],
            capture_output=True, text=True, timeout=30
        )
        if resultado.returncode == 0:
            print(f"[+] Nodo '{nombre_nodo}' detenido correctamente.")
            return True
        else:
            print(f"[-] Error al detener nodo: {resultado.stderr.strip()}")
            return False
    except FileNotFoundError:
        print("[-] Docker no encontrado. Asegúrese de que Docker está en PATH.")
        return False
    except subprocess.TimeoutExpired:
        print("[-] Timeout al detener el nodo.")
        return False


def reiniciar_nodo(nombre_nodo):
    """Reinicia un contenedor y espera hasta que is_live=true (polling con timeout)"""
    print(f"\n[+] REINICIANDO nodo '{nombre_nodo}'...")
    try:
        resultado = subprocess.run(
            ["docker", "start", nombre_nodo],
            capture_output=True, text=True, timeout=30
        )
        if resultado.returncode != 0:
            print(f"[-] Error al reiniciar nodo: {resultado.stderr.strip()}")
            return False

        print(f"[+] Nodo '{nombre_nodo}' iniciado. Esperando is_live=true...")

        start = time.perf_counter()
        while True:
            elapsed = round(time.perf_counter() - start, 1)
            if elapsed > TIMEOUT_REINICIO:
                print(f"[-] Timeout: el nodo no alcanzó is_live=true en {TIMEOUT_REINICIO}s.")
                return False

            nodos = ejecutar_sql(CLUSTER_URI, """
                SELECT is_live FROM crdb_internal.gossip_nodes
                WHERE address LIKE '%crdb-node2%';
            """)
            if nodos and nodos[0][0]:
                tiempo_real = round(time.perf_counter() - start, 1)
                print(f"[+] Nodo reincorporado. is_live=true alcanzado en {tiempo_real}s.")
                return True

            print(f"  ...esperando ({elapsed}s/{TIMEOUT_REINICIO}s)")
            time.sleep(2)

    except FileNotFoundError:
        print("[-] Docker no encontrado.")
        return False
    except subprocess.TimeoutExpired:
        print("[-] Timeout al ejecutar docker start.")
        return False


def mostrar_ranges(tabla):
    """Ejecuta SHOW RANGES y muestra la distribucion de rangos en los nodos"""
    print(f"\n[+] SHOW RANGES FROM TABLE {tabla}:")
    resultado = ejecutar_sql(CLUSTER_URI, f"SHOW RANGES FROM TABLE {tabla};")
    if resultado:
        print(f"  {'Range ID':<12}{'Start Key':<20}{'End Key':<20}{'Lease Holder':<16}{'Replicas'}")
        print(f"  {'-'*80}")
        for fila in resultado:
            start_key = str(fila[0]) if len(fila) > 0 else "?"
            end_key = str(fila[1]) if len(fila) > 1 else "?"
            range_id = str(fila[3]) if len(fila) > 3 else "?"
            lease_holder = str(fila[5]) if len(fila) > 5 else "?"
            replicas = str(fila[6]) if len(fila) > 6 else "?"
            print(f"  {range_id:<12}{start_key:<20}{end_key:<20}{lease_holder:<16}{replicas}")
    else:
        print("  [!] No se pudieron obtener los rangos (puede requerir licencia Enterprise).")


def mostrar_ranges_todas_tablas():
    """Muestra SHOW RANGES para las tablas principales"""
    for tabla in ['tickets', 'historial_estados']:
        mostrar_ranges(tabla)


def ejecutar_prueba_tolerance():
    """Secuencia completa de prueba de tolerancia a fallos"""
    print("="*65)
    print(" PRUEBA DE TOLERANCIA A FALLOS - CLÚSTER COCKROACHDB")
    print("="*65)

    # FASE 1: Estado inicial
    print("\n--- FASE 1: Estado inicial del clúster ---")
    vivos = verificar_nodos("ESTADO INICIAL - 3 NODOS")
    if vivos < 3:
        print("[-] El clúster no tiene los 3 nodos activos. Verifique con docker-compose up.")
        sys.exit(1)

    # FASE 2: Verificar operatividad antes del fallo
    print("\n--- FASE 2: Verificar operatividad completa ---")
    lectura_ok = probar_lectura()
    escritura_ok = probar_escritura()
    if not (lectura_ok and escritura_ok):
        print("[-] El clúster no opera correctamente antes de la prueba.")
        sys.exit(1)

    # FASE 3: Detener un nodo (simular fallo)
    print(f"\n--- FASE 3: Simular fallo deteniendo '{NODO_A_DETENER}' ---")
    if not detener_nodo(NODO_A_DETENER):
        print("[-] No se pudo detener el nodo. Abortando prueba.")
        sys.exit(1)

    time.sleep(30)  # Esperar 30s para que el clúster redistribuya rangos tras el fallo

    # FASE 4: Verificar quórum con nodo caído (2/3 = quórum mínimo)
    print("\n--- FASE 4: Verificar quórum con nodo caído ---")
    verificar_nodos("ESTADO CON NODO CAÍDO")

    # Verificar distribución de rangos con nodo caído
    mostrar_ranges_todas_tablas()

    print("\n[+] Verificando que el clúster sigue operativo (quórum Raft 2/3)...")
    lectura_ok = probar_lectura()
    escritura_ok = probar_escritura()

    if lectura_ok and escritura_ok:
        print("\n[+] RESULTADO: El clúster MANTIENE el servicio con 1 nodo caído.")
        print("[+] Quórum Raft intacto: 2 de 3 nodos bastan para operar.")
    else:
        print("\n[-] RESULTADO: El clúster PERDIÓ servicio con 1 nodo caído.")
        print("[-] Esto NO debería ocurrir con quórum Raft de 3 nodos.")

    # FASE 5: Reiniciar el nodo
    print(f"\n--- FASE 5: Reiniciar '{NODO_A_DETENER}' ---")
    if not reiniciar_nodo(NODO_A_DETENER):
        print("[-] No se pudo reiniciar el nodo.")
        sys.exit(1)

    # FASE 6: Verificar reincorporación del nodo
    print("\n--- FASE 6: Verificar reincorporación del nodo ---")
    vivos = verificar_nodos("ESTADO TRAS REINICIO")

    # Verificar distribución de rangos tras reincorporación
    mostrar_ranges_todas_tablas()

    if vivos >= 3:
        print("\n[+] RESULTADO FINAL: El nodo se reincorporó. Clúster completo (3/3).")
    else:
        print(f"\n[!] RESULTADO FINAL: Solo {vivos} nodos activos tras reinicio.")

    print("\n" + "="*65)
    print(" PRUEBA DE TOLERANCIA A FALLOS COMPLETADA")
    print("="*65)


if __name__ == "__main__":
    ejecutar_prueba_tolerance()
