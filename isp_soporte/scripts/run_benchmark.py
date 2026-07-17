# ==============================================================================
# SCRIPT DE AUTOMATIZACIÓN DE PRUEBAS DE RENDIMIENTO (BENCHMARK)
# REQUISITO: Comparar tiempos de ejecución entre Clúster y Nodo Único
# ==============================================================================

import psycopg2
import time
import csv
import os

# URIs de conexión a las bases de datos
CLUSTER_URI = "postgresql://root@localhost:26257/isp_soporte?sslmode=disable"
SINGLE_URI = "postgresql://root@localhost:26260/isp_soporte?sslmode=disable"

# Definición de las 5 consultas sin EXPLAIN ANALYZE para medir tiempo real en Python
QUERIES = [
    # C1: JOIN Clientes-Tickets
    """
    SELECT c.nombre, c.plan_contratado, t.asunto, t.prioridad, t.creado_at
    FROM clientes c
    INNER JOIN tickets t ON c.cliente_id = t.cliente_id
    WHERE t.estado IN ('abierto', 'en_proceso')
    ORDER BY t.creado_at DESC
    LIMIT 100;
    """,
    # C2: GROUP BY Región-Prioridad
    """
    SELECT region, prioridad, COUNT(*) as total_tickets, MAX(creado_at) as ultimo_registro
    FROM tickets
    GROUP BY region, prioridad
    ORDER BY region, total_tickets DESC;
    """,
    # C3: PK por Clave Compuesta (Se utiliza un ID genérico para la automatización)
    """
    SELECT * 
    FROM tickets 
    WHERE region = 'Centro' 
      AND ticket_id = '00000000-0000-0000-0000-000000000000';
    """,
    # C4: Consulta de Rango (Fechas)
    """
    SELECT region, asunto, prioridad, estado, creado_at
    FROM tickets
    WHERE prioridad IN ('alta', 'critica')
      AND creado_at >= NOW() - INTERVAL '30 days'
    ORDER BY creado_at ASC;
    """,
    # C5: Subconsulta Correlacionada
    """
    SELECT c.cliente_id, c.nombre, c.correo,
           (SELECT MAX(t.creado_at) FROM tickets t WHERE t.cliente_id = c.cliente_id) as fecha_ultimo_ticket
    FROM clientes c
    WHERE c.estado = 'activo'
    LIMIT 100;
    """
]


def medir_tiempo(uri, query):
    """Ejecuta una consulta y retorna el tiempo transcurrido en milisegundos"""
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(uri)
        cursor = conn.cursor()
        
        # Medición precisa de tiempo de respuesta
        start_time = time.perf_counter()
        cursor.execute(query)
        cursor.fetchall()  # Forzar recuperación total de registros
        end_time = time.perf_counter()
        
        # Conversión a milisegundos
        elapsed_ms = (end_time - start_time) * 1000
        return round(elapsed_ms, 2)
    except Exception as e:
        print(f"[-] Error al ejecutar consulta: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def ejecutar_benchmark():
    print("[+] Iniciando benchmark comparativo...")
    resultados = []

    # Ejecución de pruebas
    for i, query in enumerate(QUERIES, start=1):
        print(f"[+] Evaluando Consulta {i}...")
        t_cluster = medir_tiempo(CLUSTER_URI, query)
        t_single = medir_tiempo(SINGLE_URI, query)
        
        if t_cluster is not None and t_single is not None:
            # Calcular factor (cuántas veces más rápido es el nodo único)
            factor = round(t_cluster / t_single, 2)
            resultados.append({
                "consulta": f"Consulta {i}",
                "tiempo_cluster_ms": t_cluster,
                "tiempo_nodo_unico_ms": t_single,
                "factor_desempeno": f"{factor}x"
            })
        else:
            print(f"[-] Ocurrió un error al medir la Consulta {i}")

    # Imprimir tabla comparativa en la terminal
    print("\n" + "="*70)
    print(" RESULTADOS DEL BENCHMARK COMPARATIVO")
    print("="*70)
    print(f"{'Consulta':<15}{'Clúster (ms)':<18}{'Nodo Único (ms)':<18}{'Desempeño Relativo'}")
    print("-"*70)
    for res in resultados:
        print(f"{res['consulta']:<15}{res['tiempo_cluster_ms']:<18}{res['tiempo_nodo_unico_ms']:<18}{res['factor_desempeno']}")
    print("="*70)

    # Exportar resultados de manera obligatoria a evidencia/resultados.csv
    ruta_csv = "evidencia/resultados.csv"
    os.makedirs(os.path.dirname(ruta_csv), exist_ok=True)
    
    try:
        with open(ruta_csv, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=["consulta", "tiempo_cluster_ms", "tiempo_nodo_unico_ms", "factor_desempeno"])
            writer.writeheader()
            writer.writerows(resultados)
        print(f"[+] Resultados guardados exitosamente en: '{ruta_csv}'")
    except Exception as e:
        print(f"[-] No se pudo exportar el archivo CSV: {e}")


if __name__ == "__main__":
    ejecutar_benchmark()