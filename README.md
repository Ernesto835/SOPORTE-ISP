# ISP Soporte Tecnico — CockroachDB Distribuido

Practica experimental de bases de datos distribuidas usando CockroachDB
con 3 nodos, fragmentacion horizontal por region y pruebas de tolerancia
a fallos.

## Equipo

| Nombre | Codigo |
|--------|--------|
| Cristhian Daniel Pacheco Cardenas |  |
| Ernesto Gregory Luna Mora |  |
| Robinson Rodrigo Cando Moreno |  |

## Prerrequisitos

- Docker Desktop >= 24.0
- Docker Compose >= 2.20
- Python >= 3.10
- CockroachDB v23.1.20 (se descarga automaticamente con Docker)

## Tiempo estimado: 10-15 minutos

## Instalacion

```bash
git clone https://github.com/USUARIO/isp_soporte.git
cd isp_soporte
pip install -r requirements.txt
```

## Paso 1: Levantar el cluster

```bash
docker compose up -d
docker exec -it crdb-node1 ./cockroach init --insecure
```

## Paso 2: Verificar cluster (debe mostrar 3 nodos activos)

```bash
python scripts/verify_cluster.py
```

## Paso 3: Capturar dashboard del cluster

Abrir http://localhost:8080 en el navegador.
Tomar captura y guardar como `evidencia/dashboard.png`.

## Paso 4: Generar datos (12,500 registros)

```bash
python scripts/seed_data.py
```

## Paso 5: Benchmark comparativo

```bash
python scripts/run_benchmark.py
```

## Paso 6: Prueba de tolerancia a fallos

```bash
python scripts/fault_tolerance.py
```

## Apagar el cluster

```bash
docker compose down
```

## Estructura del proyecto

```
isp_soporte/
├── .gitignore
├── LICENSE                       # Licencia MIT
├── README.md
├── requirements.txt
├── docker-compose.yml            # Cluster de 3 nodos + nodo unico
├── sql/
│   ├── 01_schema.sql
│   ├── 02_partitions.sql
│   ├── 03_queries.sql
│   └── 04_verify_partitions.sql
├── scripts/
│   ├── seed_data.py
│   ├── verify_cluster.py
│   ├── run_benchmark.py
│   └── fault_tolerance.py
├── docs/
│   ├── isp_soporte.tex
│   ├── isp_soporte.pdf
│   └── referencias.bib
└── evidencia/
    ├── dashboard.png
    ├── video_tolerancia.mp4
    └── resultados.csv
```

## Acceso al Dashboard

- Node 1: http://localhost:8080
- Node 2: http://localhost:8081
- Node 3: http://localhost:8082
- Nodo unico: http://localhost:8083

## Solucion de problemas

| Problema | Solucion |
|----------|----------|
| Puertos 26257-26260 ocupados | Cerrar la instancia que los usa o cambiar puertos en docker-compose.yml |
| Docker no inicia | Verificar que Docker Desktop este corriendo |
| Error de conexion psycopg2 | Ejecutar `pip install -r requirements.txt` |
| Nodos no se unen | Ejecutar `docker compose down -v` y volver a levantar |
