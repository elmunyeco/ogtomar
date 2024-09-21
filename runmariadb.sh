  docker run --name mariadb -e MYSQL_ROOT_PASSWORD=hhcc -p 3306:3306 -v /home/eze/hhcc_data:/var/lib/mysql -d mariadb:latest
  docker run -p 0.0.0.0:3307:3306 --name nuevo_cardioprieto -e MARIADB_ROOT_PASSWORD=Corbis5 -d  mariadb:latest
