 CREATE TABLE `historias_clinicas` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `fechaAlta` date NOT NULL,
  `paciente_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `historia_fechaAlta_idx` (`fechaAlta`),
  KEY `idPaciente_idx` (`paciente_id`),
  CONSTRAINT `historias_clinicas_paciente_id_de33a45c_fk_pacientes_id` FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
