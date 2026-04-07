# Deploy HHCC (App + DB + Nginx)

## Archivos
- `hhcc_app_latest.tar.gz` (imagen app)
- `nuevo_cardioprieto_latest.tar.gz` (imagen DB)
- `docker-compose.yml`
- `nginx/default.conf`
- `Dockerfile` (referencia)

## Cargar imagenes
```bash
docker load -i hhcc_app_latest.tar.gz
docker load -i nuevo_cardioprieto_latest.tar.gz
```

## Levantar stack (puerto 80)
```bash
docker-compose up -d
```

## Detener / limpiar
```bash
docker-compose stop
# o
docker-compose down
```

## Acceso
- `http://<IP>/` (Nginx -> app:8000)
- DB expuesta en `3307` (host) -> `3306` (contenedor)

## Variables
Las credenciales DB por defecto:
- DB_NAME: cardioprieto
- DB_USER: root
- DB_PASSWORD: Corbis5

Si necesitas cambiar, edita `docker-compose.yml`.
