  scp /home/eze/omar/deploy/cardioprieto_dump.sql root@129.212.132.248:/root/

  Y en remoto:

  docker-compose exec -T db /bin/sh -lc "mariadb --protocol=tcp -h127.0.0.1 -P3306 -uroot -pCorbis5 -e \"CREATE DATABASE IF NOT EXISTS cardioprieto;\""
  docker-compose exec -T db /bin/sh -lc "mariadb --protocol=tcp -h127.0.0.1 -P3306 -uroot -pCorbis5 cardioprieto" < /root/deploy/cardioprieto_dump.sql
  RUN_MIGRATIONS_ON_STARTUP=0 docker-compose up -d app nginx
