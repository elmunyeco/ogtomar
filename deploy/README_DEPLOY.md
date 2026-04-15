# Deploy (Docker)

## Archivos
- `docker-compose.yml`
- `nginx/default.conf`
- `start_fresh.sh`
- `hhcc_app_latest.tar.gz`
- `nuevo_cardioprieto_latest.tar.gz`
- `cardioprieto_dump.sql`

## Arranque rapido
```sh
docker load -i hhcc_app_latest.tar.gz
docker load -i nuevo_cardioprieto_latest.tar.gz
docker-compose up -d
```

## Arranque limpio + restore automatico
```sh
./start_fresh.sh
```

`start_fresh.sh`:
- baja containers
- carga imágenes
- levanta `db`
- espera a que MariaDB acepte conexiones TCP
- restaura `cardioprieto_dump.sql` si existe
- arranca `app` y `nginx` con `RUN_MIGRATIONS_ON_STARTUP=0` cuando hay restore, para evitar que Django migre encima de una base ya cargada
- levanta `app` y `nginx`

## Restore manual
```sh
docker-compose up -d db
docker-compose exec -T db /bin/sh -lc "mariadb --protocol=tcp -h127.0.0.1 -P3306 -uroot -pCorbis5 -e \"CREATE DATABASE IF NOT EXISTS cardioprieto;\""
docker-compose exec -T db /bin/sh -lc "mariadb --protocol=tcp -h127.0.0.1 -P3306 -uroot -pCorbis5 cardioprieto" < cardioprieto_dump.sql
RUN_MIGRATIONS_ON_STARTUP=0 docker-compose up -d app nginx
```

## Detener
```sh
docker-compose stop
```

## Bajar y borrar
```sh
docker-compose down
```

## Notas
- `ALLOWED_HOSTS = ["*"]`.
- `Dockerfile` incluye librerías para PDF (pango/cairo) y `tzdata`.
