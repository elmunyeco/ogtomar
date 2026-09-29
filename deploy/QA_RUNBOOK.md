# Operacion segura de QA

El servidor de QA tiene 1 vCPU y aproximadamente 1 GiB de RAM. La suite de
tests de Django no se ejecuta en este host: crea bases y procesos temporales y
puede agotar memoria, I/O y slots de SSH.

## Regla de tests

- Ejecutar `manage.py test` o `pytest` solamente en la maquina de desarrollo o
  en un runner aislado con una base descartable.
- No ejecutar tests dentro de `hhcc_app`, ni con un contenedor temporal conectado
  a la base o a la red de QA.
- En QA se permiten solamente verificaciones livianas y de solo lectura:

```sh
docker exec hhcc_app python3 manage.py check
curl -fsS http://127.0.0.1/ >/dev/null
```

## Deploy de HHCC

1. Construir y probar la imagen fuera de QA.
2. Etiquetar la imagen activa como rollback antes de cambiar `latest`.
3. Validar la configuracion sin levantar contenedores:

```sh
cd /root/deploy
docker compose config --quiet
```

4. Recrear solamente la aplicacion. No recrear MariaDB para un cambio de codigo:

```sh
docker compose up -d --no-deps --force-recreate app
```

5. Verificar estado, logs y HTTP. No emitir recetas como smoke test:

```sh
docker inspect hhcc_app --format '{{.State.Status}} {{.State.Restarting}}'
docker logs --tail 80 hhcc_app
curl -fsS http://127.0.0.1/ >/dev/null
```

## Memoria

- `/swapfile`: 1 GiB, persistido en `/etc/fstab`.
- `vm.swappiness=10`, persistido en `/etc/sysctl.d/99-memory-headroom.conf`.
- `fwupd` queda deshabilitado en este servidor sin hardware actualizable.
- Los limites de memoria, swap y PIDs viven en los archivos Compose versionados.

## Limpieza Docker

Se pueden purgar cache de build, imagenes sin tag y volumenes anonimos sin
contenedores asociados. No borrar volumenes nombrados ni el volumen montado en
`nuevo_cardioprieto` sin un backup verificado.

Antes de una limpieza de volumenes:

```sh
docker volume ls
docker ps -a --format '{{.Names}} {{.Mounts}}'
docker system df -v
```
