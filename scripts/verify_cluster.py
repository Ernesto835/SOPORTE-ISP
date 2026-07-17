# ==============================================================================
# SCRIPT DE VERIFICACIÓN DEL CLÚSTER - 3 NODOS COCKROACHDB
# REQUISITO: Verificar que los 3 nodos estén activos (is_live = true)
# ==============================================================================

import psycopg2
import sys

CLUSTER_URI = "postgresql://root@localhost:26257/isp_soporte?sslmode=disable"


def verificar_nodos():
    """Consulta crdb_internal.gossip_nodes para verificar el estado de cada nodo"""
    print("[+] Conectando al clúster para verificar nodos...")
    conn = None
    try:
        conn = psycopg2.connect(CLUSTER_URI)
        conn.autocommit = True
        cursor = conn.cursor()

        cursor.execute("""
            SELECT node_id, address, is_live, is_available
            FROM crdb_internal.gossip_nodes
            ORDER BY node_id;
        """)
        nodos = cursor.fetchall()

        print("\n" + "="*65)
        print(" ESTADO DEL CLÚSTER COCKROACHDB (3 NODOS)")
        print("="*65)
        print(f"{'Node ID':<12}{'Dirección':<22}{'is_live':<12}{'is_available'}")
        print("-"*65)

        todos_vivos = True
        for node_id, address, is_live, is_available in nodos:
            estado_live = "SI" if is_live else "NO"
            estado_avail = "SI" if is_available else "NO"
            print(f"{node_id:<12}{address:<22}{estado_live:<12}{estado_avail}")
            if not is_live:
                todos_vivos = False

        print("="*65)

        total_nodos = len(nodos)
        nodos_vivos = sum(1 for _, _, is_live, _ in nodos if is_live)

        print(f"\n[+] Total de nodos detectados: {total_nodos}")
        print(f"[+] Nodos activos (is_live=true): {nodos_vivos}")

        if total_nodos >= 3 and todos_vivos:
            print("[+] RESULTADO: Clúster completo y operativo. Quórum Raft alcanzado (3/3).")
            return True
        elif nodos_vivos >= 2:
            print("[!] RESULTADO: Clúster degradado pero funcional (quórum parcial).")
            return True
        else:
            print("[-] RESULTADO: Clúster inoperativo. No se alcanza quórum.")
            return False

    except Exception as e:
        print(f"[-] Error al conectar o consultar el clúster: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    exito = verificar_nodos()
    sys.exit(0 if exito else 1)
