# QA Full Deploy (contenedores + datos + usuarios)

## 1) En el host origen (este servidor)

### A. Exportar imágenes Docker

```
docker save -o /home/eze/omar/migracion_db/qa_images.tar.gz hhcc_app:latest nuevo_cardioprieto:latest nginx:alpine
```

> Si tu nginx usa otra imagen/tag, reemplazar `nginx:alpine`.

### B. Exportar datos + users (bundle)

```bash
# bundle ya generado
tar -czf /home/eze/omar/migracion_db/qa_bundle.tar.gz -C /home/eze/omar/migracion_db qa_bundle
```

### C. Copiar todo a QA

```bash
scp /home/eze/omar/migracion_db/qa_images.tar.gz usuario@129.212.132.248:/root/deploy/
scp /home/eze/omar/migracion_db/qa_bundle.tar.gz usuario@129.212.132.248:/root/deploy/
scp /home/eze/omar/deploy/docker-compose.yml usuario@129.212.132.248:/root/deploy/
scp /home/eze/omar/nginx/default.conf usuario@129.212.132.248:/root/deploy/
```

---

## 2) En el host QA

### A. Cargar imágenes

```bash
cd /root/deploy
docker load -i qa_images.tar.gz
```

### B. Levantar stack

```bash
docker-compose up -d
```

### C. Restaurar base + users

```bash
tar -zxvf qa_bundle.tar.gz
cd qa_bundle
./restore_qa.sh
```

> `restore_qa.sh` aplica **schema + data + auth_dump**.

### D. (Opcional) Forzar usuarios si hiciera falta

```bash
APP_CONTAINER=hhcc_app /home/eze/omar/migracion_db/fix_users.sh
```

### E. Arranque/paro sin borrar contenedores

```bash
docker-compose stop
docker-compose start
```

---

## Usuarios
- `eze / Furosemida` (admin)
- `omar / Corbis5`