# Docker (App + DB) - Integracion HHCC

Fecha: 2026-04-04

## Objetivo
- Levantar **la base MySQL** en Docker con nombre **`nuevo_cardioprieto`**.
- Levantar la app **despues** de que la DB este lista.
- Generar `docker save` de **ambas** imagenes para copiarlas y desplegarlas online.

## Requisitos
- Docker y docker-compose instalados.
- Archivo `nuevo_cardioprieto.sql.gz` en la raiz del repo (si corresponde importar).

## 1) Base de datos (container: `nuevo_cardioprieto`)

### Crear/levantar DB
```bash
# Crea el contenedor con el nombre requerido
# Puerto local 3307 -> contenedor 3306

docker run -d \
  --name nuevo_cardioprieto \
  -e MARIADB_ROOT_PASSWORD=Corbis5 \
  -p 3307:3306 \
  mariadb:10.5
```

### Verificar DB lista
```bash
docker logs -f nuevo_cardioprieto
```

## 2) App (depende de `nuevo_cardioprieto`)

### Dockerfile (app)
Se genera automaticamente desde `hhcc_installer.sh`, o puede crearse manualmente. El contenedor debe usar los env vars:
- `DB_HOST=nuevo_cardioprieto`
- `DB_PORT=3306`
- `DB_NAME=cardioprieto`
- `DB_USER=root`
- `DB_PASSWORD=Corbis5`

### docker-compose.yml (con dependencia)
Ejemplo minimo (app depende del contenedor DB ya creado):

```yaml
version: '3'
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: hhcc_app
    restart: always
    ports:
      - "8000:8000"
    volumes:
      - ./hhcc:/app
    environment:
      - DB_HOST=nuevo_cardioprieto
      - DB_PORT=3306
      - DB_NAME=cardioprieto
      - DB_USER=root
      - DB_PASSWORD=Corbis5
    depends_on:
      - dbwait

  # Servicio dummy para esperar DB
  dbwait:
    image: busybox
    command: sh -c "until nc -z nuevo_cardioprieto 3306; do sleep 1; done"
```

> Nota: el contenedor `nuevo_cardioprieto` existe **fuera** de este compose. `dbwait` solo bloquea el arranque hasta que la DB responda.

### Levantar app
```bash
docker-compose up -d
```

## 3) Guardar imagenes (docker save)

### Guardar imagen de la app
```bash
# Build y guardar

docker build -t hhcc_app:latest .
docker save -o hhcc_app_latest.tar hhcc_app:latest
```

### Guardar imagen de la DB (nuevo_cardioprieto)
```bash
# La imagen base es mariadb:10.5

docker save -o nuevo_cardioprieto_mariadb_10_5.tar mariadb:10.5
```

## 4) Restaurar en server online
```bash
# Cargar imagenes

docker load -i hhcc_app_latest.tar
docker load -i nuevo_cardioprieto_mariadb_10_5.tar

# Levantar DB

docker run -d \
  --name nuevo_cardioprieto \
  -e MARIADB_ROOT_PASSWORD=Corbis5 \
  -p 3307:3306 \
  mariadb:10.5

# Levantar app

docker run -d \
  --name hhcc_app \
  -p 8000:8000 \
  -e DB_HOST=nuevo_cardioprieto \
  -e DB_PORT=3306 \
  -e DB_NAME=cardioprieto \
  -e DB_USER=root \
  -e DB_PASSWORD=Corbis5 \
  hhcc_app:latest
```

## 5) Chequeos rapidos
```bash
docker ps
curl -I http://localhost:8000/
```

