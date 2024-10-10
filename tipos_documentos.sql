LOCK TABLES `tipos_documentos` WRITE;
ALTER TABLE `tipos_documentos` DISABLE KEYS;
INSERT INTO `tipos_documentos` VALUES
(1,'DNI','Documento  Nacional de Identidad'),
(2,'CI','Cédula de Identidad'),
(3,'LE','Libreta de Enrolamiento'),
(4,'LC','Libreta Cívica');

