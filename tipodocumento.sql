LOCK TABLES `tipodocumento` WRITE;
ALTER TABLE `tipodocumento` DISABLE KEYS;
INSERT INTO `tipodocumento` VALUES
(1,'DNI','Documento  Nacional de Identidad'),
(2,'CI','Cédula de Identidad'),
(3,'LE','Libreta de Enrolamiento'),
(4,'LC','Libreta Cívica');

