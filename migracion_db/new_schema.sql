/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.6-MariaDB, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: cardioprieto
-- ------------------------------------------------------
-- Server version	11.5.2-MariaDB-ubu2404

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `auth_group`
--

DROP TABLE IF EXISTS `auth_group`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(150) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_group_permissions`
--

DROP TABLE IF EXISTS `auth_group_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_group_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `group_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_group_permissions_group_id_permission_id_0cd325b0_uniq` (`group_id`,`permission_id`),
  KEY `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_group_permissio_permission_id_84c5c92e_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_group_permissions_group_id_b120cbf9_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_permission`
--

DROP TABLE IF EXISTS `auth_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_permission` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `content_type_id` int(11) NOT NULL,
  `codename` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_permission_content_type_id_codename_01ab375a_uniq` (`content_type_id`,`codename`),
  CONSTRAINT `auth_permission_content_type_id_2f476e4b_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user`
--

DROP TABLE IF EXISTS `auth_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `password` varchar(128) NOT NULL,
  `last_login` datetime(6) DEFAULT NULL,
  `is_superuser` tinyint(1) NOT NULL,
  `username` varchar(150) NOT NULL,
  `first_name` varchar(150) NOT NULL,
  `last_name` varchar(150) NOT NULL,
  `email` varchar(254) NOT NULL,
  `is_staff` tinyint(1) NOT NULL,
  `is_active` tinyint(1) NOT NULL,
  `date_joined` datetime(6) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_groups`
--

DROP TABLE IF EXISTS `auth_user_groups`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_groups` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `group_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_groups_user_id_group_id_94350c0c_uniq` (`user_id`,`group_id`),
  KEY `auth_user_groups_group_id_97559544_fk_auth_group_id` (`group_id`),
  CONSTRAINT `auth_user_groups_group_id_97559544_fk_auth_group_id` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`),
  CONSTRAINT `auth_user_groups_user_id_6a12ed8b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_user_user_permissions`
--

DROP TABLE IF EXISTS `auth_user_user_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `auth_user_user_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `permission_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `auth_user_user_permissions_user_id_permission_id_14a6b632_uniq` (`user_id`,`permission_id`),
  KEY `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` (`permission_id`),
  CONSTRAINT `auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm` FOREIGN KEY (`permission_id`) REFERENCES `auth_permission` (`id`),
  CONSTRAINT `auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `carotidas`
--

DROP TABLE IF EXISTS `carotidas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `carotidas` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `com_derecha` varchar(512) DEFAULT NULL,
  `int_derecha` varchar(512) DEFAULT NULL,
  `ext_derecha` varchar(512) DEFAULT NULL,
  `com_izquierda` varchar(512) DEFAULT NULL,
  `int_izquierda` varchar(512) DEFAULT NULL,
  `ext_izquierda` varchar(512) DEFAULT NULL,
  `art_vertebrales` varchar(255) DEFAULT NULL,
  `sugerencias` varchar(255) DEFAULT NULL,
  `id_com_der` int(10) unsigned NOT NULL CHECK (`id_com_der` >= 0),
  `id_com_izq` int(10) unsigned NOT NULL CHECK (`id_com_izq` >= 0),
  `esp_int_med_der` decimal(4,2) DEFAULT NULL,
  `esp_int_med_izq` decimal(4,2) DEFAULT NULL,
  `historia_id` bigint(20) NOT NULL,
  `fecha_estudio` date NOT NULL,
  PRIMARY KEY (`id`),
  KEY `carotidas_historia_idx` (`historia_id`),
  KEY `carotidas_com_idx` (`id_com_der`,`id_com_izq`),
  CONSTRAINT `carotidas_historia_id_f5293af1_fk_historias_clinicas_id` FOREIGN KEY (`historia_id`) REFERENCES `historias_clinicas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `comentarios`
--

DROP TABLE IF EXISTS `comentarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `comentarios` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `comentario` text CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `idHistoriaClinica` int(10) unsigned NOT NULL,
  `idTipoComentario` int(10) unsigned NOT NULL,
  `proteger` tinyint(1) unsigned NOT NULL,
  `eliminado` tinyint(4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fecha` (`fecha`,`idHistoriaClinica`,`idTipoComentario`),
  KEY `proteger` (`proteger`)
) ENGINE=MyISAM AUTO_INCREMENT=80817 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `comentarios_visitas`
--

DROP TABLE IF EXISTS `comentarios_visitas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `comentarios_visitas` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `fecha` datetime(6) NOT NULL,
  `comentarios` longtext NOT NULL,
  `idHistoriaClinica` bigint(20) NOT NULL,
  `tipo` varchar(5) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `comentarios_fecha_f1595a_idx` (`fecha`),
  KEY `comentarios_idHisto_e55c6a_idx` (`idHistoriaClinica`),
  KEY `comentarios_fecha_f65e9a_idx` (`fecha`,`idHistoriaClinica`),
  CONSTRAINT `comentarios_visitas_idHistoriaClinica_eec29d40_fk_historias` FOREIGN KEY (`idHistoriaClinica`) REFERENCES `historias_clinicas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15785 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `conclusiones_ecocardiograma`
--

DROP TABLE IF EXISTS `conclusiones_ecocardiograma`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `conclusiones_ecocardiograma` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `situs` int(11) DEFAULT NULL,
  `comentario_situs` longtext DEFAULT NULL,
  `vasos_normoimplantados` int(11) DEFAULT NULL,
  `comentario_vasos` longtext DEFAULT NULL,
  `concordancia_atrioventricular` int(11) DEFAULT NULL,
  `comentario_concordancia` longtext DEFAULT NULL,
  `auricula_izq` varchar(100) NOT NULL,
  `ventriculo_izq` varchar(100) NOT NULL,
  `funcion_sistolica` int(11) DEFAULT NULL,
  `funcion_diastolica` int(11) DEFAULT NULL,
  `motilidad_segmentaria` int(11) DEFAULT NULL,
  `comentario_motilidad` longtext DEFAULT NULL,
  `valvula_aortica` varchar(50) NOT NULL,
  `comentario_valvula_aortica` longtext DEFAULT NULL,
  `valvula_mitral` varchar(50) NOT NULL,
  `comentario_valvula_mitral` longtext DEFAULT NULL,
  `valvula_tricuspide` varchar(50) NOT NULL,
  `comentario_valvula_tricuspide` longtext DEFAULT NULL,
  `valvula_pulmonar` varchar(50) NOT NULL,
  `comentario_valvula_pulmonar` longtext DEFAULT NULL,
  `pericardio` int(11) DEFAULT NULL,
  `comentario_pericardio` longtext DEFAULT NULL,
  `defectos_congenitos` int(11) DEFAULT NULL,
  `comentario_defectos` longtext DEFAULT NULL,
  `conclusion_texto` longtext NOT NULL,
  `comentario_final` longtext NOT NULL,
  `estudio_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `estudio_id` (`estudio_id`),
  CONSTRAINT `conclusiones_ecocard_estudio_id_36723ed6_fk_estudios_` FOREIGN KEY (`estudio_id`) REFERENCES `estudios_ecocardiograma` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `condiciones_medicas`
--

DROP TABLE IF EXISTS `condiciones_medicas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `condiciones_medicas` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(100) NOT NULL,
  `orden` int(11) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `condiciones_medicas_historias`
--

DROP TABLE IF EXISTS `condiciones_medicas_historias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `condiciones_medicas_historias` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `historia_id` bigint(20) NOT NULL,
  `condicion_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_historia_condicion` (`historia_id`,`condicion_id`),
  KEY `condicion_id` (`condicion_id`),
  CONSTRAINT `condiciones_medicas_historias_ibfk_1` FOREIGN KEY (`historia_id`) REFERENCES `historias_clinicas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `condiciones_medicas_historias_ibfk_2` FOREIGN KEY (`condicion_id`) REFERENCES `condiciones_medicas` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=736 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_admin_log`
--

DROP TABLE IF EXISTS `django_admin_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_admin_log` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `action_time` datetime(6) NOT NULL,
  `object_id` longtext DEFAULT NULL,
  `object_repr` varchar(200) NOT NULL,
  `action_flag` smallint(5) unsigned NOT NULL CHECK (`action_flag` >= 0),
  `change_message` longtext NOT NULL,
  `content_type_id` int(11) DEFAULT NULL,
  `user_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `django_admin_log_content_type_id_c4bce8eb_fk_django_co` (`content_type_id`),
  KEY `django_admin_log_user_id_c564eba6_fk_auth_user_id` (`user_id`),
  CONSTRAINT `django_admin_log_content_type_id_c4bce8eb_fk_django_co` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`),
  CONSTRAINT `django_admin_log_user_id_c564eba6_fk_auth_user_id` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_content_type`
--

DROP TABLE IF EXISTS `django_content_type`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_content_type` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `app_label` varchar(100) NOT NULL,
  `model` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `django_content_type_app_label_model_76bd3d3b_uniq` (`app_label`,`model`)
) ENGINE=InnoDB AUTO_INCREMENT=23 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_migrations`
--

DROP TABLE IF EXISTS `django_migrations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_migrations` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `app` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `applied` datetime(6) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=63 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `django_session`
--

DROP TABLE IF EXISTS `django_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `django_session` (
  `session_key` varchar(40) NOT NULL,
  `session_data` longtext NOT NULL,
  `expire_date` datetime(6) NOT NULL,
  PRIMARY KEY (`session_key`),
  KEY `django_session_expire_date_a5c62663` (`expire_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `estudios_ecocardiograma`
--

DROP TABLE IF EXISTS `estudios_ecocardiograma`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `estudios_ecocardiograma` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `peso` decimal(5,2) DEFAULT NULL,
  `talla` decimal(3,2) DEFAULT NULL,
  `presion_sistolica` int(11) DEFAULT NULL,
  `presion_diastolica` int(11) DEFAULT NULL,
  `auricula_izq_diametro` decimal(5,2) DEFAULT NULL,
  `area_auricula_izq` decimal(5,2) DEFAULT NULL,
  `plano_valvular_aortico` decimal(5,2) DEFAULT NULL,
  `septum_diastole` decimal(5,2) DEFAULT NULL,
  `pared_diastole` decimal(5,2) DEFAULT NULL,
  `vent_izq_diastolico` decimal(5,2) DEFAULT NULL,
  `vent_izq_sistolico` decimal(5,2) DEFAULT NULL,
  `diametro_tsvi` decimal(5,2) DEFAULT NULL,
  `fraccion_simpson` decimal(5,2) DEFAULT NULL,
  `fraccion_acortamiento` decimal(5,2) DEFAULT NULL,
  `tapse` decimal(5,2) DEFAULT NULL,
  `vent_derecho` decimal(5,2) DEFAULT NULL,
  `valvula_pulmonar` decimal(5,2) DEFAULT NULL,
  `valvula_aortica` decimal(5,2) DEFAULT NULL,
  `tracto_vent_izq` decimal(5,2) DEFAULT NULL,
  `onda_e_mitral` decimal(5,2) DEFAULT NULL,
  `onda_a_mitral` decimal(5,2) DEFAULT NULL,
  `onda_e_tricuspidea` decimal(5,2) DEFAULT NULL,
  `onda_a_tricuspidea` decimal(5,2) DEFAULT NULL,
  `strain_longitudinal` decimal(5,2) DEFAULT NULL,
  `historia_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `estudios_ecocardiogr_historia_id_fabd9970_fk_historias` (`historia_id`),
  CONSTRAINT `estudios_ecocardiogr_historia_id_fabd9970_fk_historias` FOREIGN KEY (`historia_id`) REFERENCES `historias_clinicas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `historias_clinicas`
--

DROP TABLE IF EXISTS `historias_clinicas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historias_clinicas` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `fechaAlta` date NOT NULL,
  `paciente_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `historia_fechaAlta_idx` (`fechaAlta`),
  KEY `historia_paciente_idx` (`paciente_id`),
  CONSTRAINT `historias_clinicas_paciente_id_de33a45c_fk_pacientes_id` FOREIGN KEY (`paciente_id`) REFERENCES `pacientes` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11565 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `indicaciones_visitas`
--

DROP TABLE IF EXISTS `indicaciones_visitas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `indicaciones_visitas` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `historia_clinica_id` bigint(20) NOT NULL,
  `medicamento` text NOT NULL,
  `ochoHoras` text DEFAULT NULL,
  `doceHoras` text DEFAULT NULL,
  `dieciochoHoras` text DEFAULT NULL,
  `veintiunaHoras` text DEFAULT NULL,
  `fecha` date NOT NULL,
  `eliminado` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idHC` (`historia_clinica_id`),
  KEY `ind_hist_fecha_idx` (`historia_clinica_id`,`fecha`),
  KEY `indicaciones_historia_idx` (`historia_clinica_id`)
) ENGINE=InnoDB AUTO_INCREMENT=18618 DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mmii`
--

DROP TABLE IF EXISTS `mmii`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `mmii` (
  `idMMII` int(11) NOT NULL AUTO_INCREMENT,
  `artFemComunDerecha` longtext DEFAULT NULL,
  `artFemSuperficialDerecha` longtext DEFAULT NULL,
  `artFemProfundaDerecha` longtext DEFAULT NULL,
  `artPopliteaDerecha` longtext DEFAULT NULL,
  `artInfrapatelaresDerecha` longtext DEFAULT NULL,
  `artFemComunIzquierda` longtext DEFAULT NULL,
  `artFemSuperficialIzquierda` longtext DEFAULT NULL,
  `artFemProfundaIzquierda` longtext DEFAULT NULL,
  `artPopliteaIzquierda` longtext DEFAULT NULL,
  `artInfrapatelaresIzquierda` longtext DEFAULT NULL,
  `conclusion` longtext DEFAULT NULL,
  `idHC` bigint(20) NOT NULL,
  `fecha_estudio` date NOT NULL,
  PRIMARY KEY (`idMMII`),
  KEY `mmii_historia_idx` (`idHC`),
  CONSTRAINT `mmii_idHC_4de50727_fk_historias_clinicas_id` FOREIGN KEY (`idHC`) REFERENCES `historias_clinicas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pacientes`
--

DROP TABLE IF EXISTS `pacientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pacientes` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `numDoc` varchar(50) NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `apellido` varchar(50) NOT NULL,
  `fechaNac` date DEFAULT NULL,
  `sexo` varchar(1) NOT NULL,
  `mail` varchar(50) DEFAULT NULL,
  `direccion` varchar(100) DEFAULT NULL,
  `localidad` varchar(60) DEFAULT NULL,
  `obraSocial` varchar(50) NOT NULL,
  `plan` varchar(50) DEFAULT NULL,
  `afiliado` varchar(50) NOT NULL,
  `telefono` varchar(50) NOT NULL,
  `celular` varchar(50) NOT NULL,
  `profesion` varchar(50) NOT NULL,
  `referente` varchar(50) DEFAULT NULL,
  `fechaAlta` date NOT NULL,
  `deBaja` tinyint(1) NOT NULL,
  `idTipoDoc_id` bigint(20) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `nombre_paciente_idx` (`nombre`),
  KEY `apellido_paciente_idx` (`apellido`),
  KEY `paciente_fechaAlta_idx` (`fechaAlta`),
  KEY `pacientes_idTipoDoc_id_6d4a5435` (`idTipoDoc_id`),
  KEY `pacientes_tipo_doc_idx` (`idTipoDoc_id`),
  FULLTEXT KEY `nombre_apellido_idx` (`nombre`,`apellido`),
  CONSTRAINT `pacientes_idTipoDoc_id_6d4a5435_fk_tipos_documentos_id` FOREIGN KEY (`idTipoDoc_id`) REFERENCES `tipos_documentos` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=11565 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `random_hc`
--

DROP TABLE IF EXISTS `random_hc`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `random_hc` (
  `idHistoriaClinica` int(10) unsigned NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `segmentos_ecocardiograma`
--

DROP TABLE IF EXISTS `segmentos_ecocardiograma`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `segmentos_ecocardiograma` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `numero_segmento` int(11) NOT NULL,
  `estado` int(11) NOT NULL,
  `estudio_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `segmentos_ecocardiograma_estudio_id_numero_segmen_458343a8_uniq` (`estudio_id`,`numero_segmento`),
  CONSTRAINT `segmentos_ecocardiog_estudio_id_02c35c49_fk_estudios_` FOREIGN KEY (`estudio_id`) REFERENCES `estudios_ecocardiograma` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `signos_vitales`
--

DROP TABLE IF EXISTS `signos_vitales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `signos_vitales` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `fecha` date NOT NULL,
  `presion_sistolica` int(11) DEFAULT NULL,
  `presion_diastolica` int(11) DEFAULT NULL,
  `peso` decimal(5,2) DEFAULT NULL,
  `glucemia` int(11) DEFAULT NULL,
  `colesterol` int(11) DEFAULT NULL,
  `historia_id` bigint(20) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `signos_vitales_historia_id_01c747bc_fk_historias_clinicas_id` (`historia_id`),
  KEY `signos_vitales_historia_idx` (`historia_id`),
  KEY `signos_vitales_fecha_idx` (`fecha`),
  CONSTRAINT `signos_vitales_historia_id_01c747bc_fk_historias_clinicas_id` FOREIGN KEY (`historia_id`) REFERENCES `historias_clinicas` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stress`
--

DROP TABLE IF EXISTS `stress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `stress` (
  `idStress` int(11) NOT NULL AUTO_INCREMENT,
  `indicacionEstudio` longtext DEFAULT NULL,
  `tipoApremio` longtext DEFAULT NULL,
  `medicacionMomentoEstudio` longtext DEFAULT NULL,
  `medicoSolicitante` longtext DEFAULT NULL,
  `frecuenciaCardiacaBasal` longtext DEFAULT NULL,
  `frecuenciaCardiacaMaxima` longtext DEFAULT NULL,
  `presionArterialBasalInicial` longtext DEFAULT NULL,
  `presionArterialBasalFinal` longtext DEFAULT NULL,
  `presionArterialMaximaInicial` longtext DEFAULT NULL,
  `presionArterialMaximaFinal` longtext DEFAULT NULL,
  `informeErgometria` longtext DEFAULT NULL,
  `datosEcocardiograficosBasales` longtext DEFAULT NULL,
  `datosEcocardiograficosPostEsfuerzoInmediato` longtext DEFAULT NULL,
  `conclusion` longtext DEFAULT NULL,
  `idHC` bigint(20) NOT NULL,
  `fecha_estudio` date DEFAULT NULL,
  PRIMARY KEY (`idStress`),
  KEY `stress_historia_idx` (`idHC`),
  CONSTRAINT `stress_idHC_73cc9ce7_fk_historias_clinicas_id` FOREIGN KEY (`idHC`) REFERENCES `historias_clinicas` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipos_documentos`
--

DROP TABLE IF EXISTS `tipos_documentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tipos_documentos` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `nombre_tipodocumento_idx` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-04-07  0:21:55
