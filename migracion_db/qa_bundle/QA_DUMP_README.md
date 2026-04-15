# QA DB dump/restore

## Archivos
- `cardioprieto_schema.sql`: esquema completo (tablas, índices, triggers)
- `cardioprieto_data.sql`: datos (INSERTs)

## Dump (origen)

```bash
mariadb-dump -h 127.0.0.1 -P 3307 -uroot -pCorbis5 --routines --triggers --no-data cardioprieto > cardioprieto_schema.sql
mariadb-dump -h 127.0.0.1 -P 3307 -uroot -pCorbis5 --no-create-info --skip-triggers cardioprieto > cardioprieto_data.sql
```

## Restore (QA)

```bash
# crear db vacia
mariadb -h 127.0.0.1 -P 3307 -uroot -pCorbis5 -e "DROP DATABASE IF EXISTS cardioprieto; CREATE DATABASE cardioprieto CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# aplicar esquema y datos
mariadb -h 127.0.0.1 -P 3307 -uroot -pCorbis5 cardioprieto < cardioprieto_schema.sql
mariadb -h 127.0.0.1 -P 3307 -uroot -pCorbis5 cardioprieto < cardioprieto_data.sql
```

## Transferencia (desde este host)

```bash
scp -r /home/eze/omar/migracion_db/qa_dump usuario@QA_HOST:/ruta/destino/
```

> Ajustar `usuario`, `QA_HOST`, puerto y ruta según el entorno de QA.
