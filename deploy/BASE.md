  scp /home/eze/omar/deploy/cardioprieto_dump.sql root@129.212.132.248:/root/

  Y en remoto:

  docker-compose exec -T db /bin/sh -lc "mariadb -uroot -pCorbis5 -e \"CREATE DATABASE IF NOT EXISTS cardioprieto;\""
  docker-compose exec -T db /bin/sh -lc "mariadb -uroot -pCorbis5 cardioprieto" < /root/deploy/cardioprieto_dump.sql
