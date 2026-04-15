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
-- Table structure for table `carotidas`
--

DROP TABLE IF EXISTS `carotidas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `carotidas` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `idHC` int(10) unsigned NOT NULL,
  `comDerecha` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `intDerecha` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `extDerecha` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `comIzquierda` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `intIzquierda` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `extIzquierda` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `artVertebrales` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `sugerencias` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `idComDer` int(10) unsigned NOT NULL,
  `idComIzq` int(10) unsigned NOT NULL,
  `espIntMedDer` decimal(4,2) DEFAULT NULL,
  `espIntMedIzq` decimal(4,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idHC` (`idHC`),
  KEY `comentarioComDer` (`idComDer`,`idComIzq`)
) ENGINE=InnoDB AUTO_INCREMENT=3971 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
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
-- Table structure for table `doppler`
--

DROP TABLE IF EXISTS `doppler`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `doppler` (
  `idDoppler` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `idHC` int(10) unsigned NOT NULL,
  `artFemComunDerecha` text NOT NULL,
  `artFemSuperficialDerecha` text NOT NULL,
  `artFemProfundaDerecha` text NOT NULL,
  `artPopliteaDerecha` text NOT NULL,
  `artInfrapatelaresDerecha` text NOT NULL,
  `artFemComunIzquierda` text NOT NULL,
  `artFemSuperficialIzquierda` text NOT NULL,
  `artFemProfundaIzquierda` text NOT NULL,
  `artPopliteaIzquierda` text NOT NULL,
  `artInfrapatelaresIzquierda` text NOT NULL,
  `conclusion` text NOT NULL,
  PRIMARY KEY (`idDoppler`),
  KEY `idHC` (`idHC`)
) ENGINE=InnoDB AUTO_INCREMENT=68 DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eco_analisisbidimensional`
--

DROP TABLE IF EXISTS `eco_analisisbidimensional`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eco_analisisbidimensional` (
  `idEstudioeco` int(10) unsigned NOT NULL,
  `campo1` float unsigned NOT NULL,
  `campo2` float unsigned NOT NULL,
  `campo3` float unsigned NOT NULL,
  `campo4` float unsigned NOT NULL,
  `campo5` float unsigned NOT NULL,
  `campo6` float unsigned NOT NULL,
  `campo7` float unsigned NOT NULL,
  `campo8` float unsigned NOT NULL,
  `campo9` float unsigned NOT NULL,
  `campo10` float unsigned NOT NULL,
  `campo11` float unsigned NOT NULL,
  `campo12` float unsigned NOT NULL,
  UNIQUE KEY `idEstudioeco` (`idEstudioeco`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eco_analisisdoppler`
--

DROP TABLE IF EXISTS `eco_analisisdoppler`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eco_analisisdoppler` (
  `idEstudioeco` int(10) unsigned NOT NULL,
  `vPulmonar` float unsigned DEFAULT NULL,
  `vAortica` float unsigned DEFAULT NULL,
  `vIzquierdo` float unsigned DEFAULT NULL,
  `vMitralE` float unsigned DEFAULT NULL,
  `vMitralA` float unsigned DEFAULT NULL,
  `vTricuspideaE` float unsigned DEFAULT NULL,
  `vTricuspideaA` float unsigned DEFAULT NULL,
  `strainGlobal` float unsigned DEFAULT NULL,
  UNIQUE KEY `idEstudioeco` (`idEstudioeco`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eco_conclusionB`
--

DROP TABLE IF EXISTS `eco_conclusionB`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eco_conclusionB` (
  `idEstudioeco` int(10) unsigned NOT NULL,
  `conclusionB` text DEFAULT NULL,
  UNIQUE KEY `idEstudioeco` (`idEstudioeco`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eco_conclusiones`
--

DROP TABLE IF EXISTS `eco_conclusiones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eco_conclusiones` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `idEstudioeco` int(10) unsigned NOT NULL,
  `orden` tinyint(3) unsigned NOT NULL,
  `valor` varchar(20) NOT NULL,
  `comentario` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idEstudioeco` (`idEstudioeco`)
) ENGINE=InnoDB AUTO_INCREMENT=176011 DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `eco_segmentos`
--

DROP TABLE IF EXISTS `eco_segmentos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `eco_segmentos` (
  `idEstudioeco` int(10) unsigned NOT NULL,
  `s1` tinyint(2) unsigned DEFAULT NULL,
  `s2` tinyint(2) unsigned DEFAULT NULL,
  `s3` tinyint(2) unsigned DEFAULT NULL,
  `s4` tinyint(2) unsigned DEFAULT NULL,
  `s5` tinyint(2) unsigned DEFAULT NULL,
  `s6` tinyint(2) unsigned DEFAULT NULL,
  `s7` tinyint(2) unsigned DEFAULT NULL,
  `s8` tinyint(2) unsigned DEFAULT NULL,
  `s9` tinyint(2) unsigned DEFAULT NULL,
  `s10` tinyint(2) unsigned DEFAULT NULL,
  `s11` tinyint(2) unsigned DEFAULT NULL,
  `s12` tinyint(2) unsigned DEFAULT NULL,
  `s13` tinyint(2) unsigned DEFAULT NULL,
  `s14` tinyint(2) unsigned DEFAULT NULL,
  `s15` tinyint(2) unsigned DEFAULT NULL,
  `s16` tinyint(2) unsigned DEFAULT NULL,
  UNIQUE KEY `idEstudioeco` (`idEstudioeco`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ecocardiograma`
--

DROP TABLE IF EXISTS `ecocardiograma`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ecocardiograma` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `peso` float unsigned NOT NULL,
  `talla` float unsigned NOT NULL,
  `idHC` int(11) NOT NULL,
  `fecha` date NOT NULL,
  `comFinal` varchar(700) DEFAULT NULL,
  `pad` int(3) unsigned DEFAULT NULL,
  `pas` int(3) unsigned DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12625 DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `enfermedades`
--

DROP TABLE IF EXISTS `enfermedades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `enfermedades` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `orden` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `orden` (`orden`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `estudios`
--

DROP TABLE IF EXISTS `estudios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `estudios` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `idHC` int(10) unsigned NOT NULL,
  `idEstudio` int(10) unsigned NOT NULL,
  `idTipoEstudio` int(10) unsigned NOT NULL,
  `fecha` date NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16803 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `estudios_comentarios`
--

DROP TABLE IF EXISTS `estudios_comentarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `estudios_comentarios` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `comentario` text CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=30 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `hclinica_enfermedades`
--

DROP TABLE IF EXISTS `hclinica_enfermedades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `hclinica_enfermedades` (
  `idHC` int(10) unsigned NOT NULL,
  `idEnfermedad` int(10) unsigned NOT NULL,
  PRIMARY KEY (`idHC`,`idEnfermedad`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `historiaclinica`
--

DROP TABLE IF EXISTS `historiaclinica`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historiaclinica` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `fechaAlta` date NOT NULL,
  `idPaciente` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fechaAlta` (`fechaAlta`,`idPaciente`)
) ENGINE=MyISAM AUTO_INCREMENT=11565 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `indicaciones`
--

DROP TABLE IF EXISTS `indicaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `indicaciones` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `idHC` int(10) unsigned NOT NULL,
  `medicamento` text NOT NULL,
  `ochoHoras` text DEFAULT NULL,
  `doceHoras` text DEFAULT NULL,
  `dieciochoHoras` text DEFAULT NULL,
  `veintiunaHoras` text DEFAULT NULL,
  `fecha` date NOT NULL,
  `eliminado` bit(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idHC` (`idHC`)
) ENGINE=InnoDB AUTO_INCREMENT=18612 DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pacientes`
--

DROP TABLE IF EXISTS `pacientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `pacientes` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `idTipoDoc` int(10) unsigned NOT NULL,
  `numDoc` int(10) unsigned NOT NULL,
  `nombre` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `apellido` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `fechaNac` date NOT NULL,
  `sexo` char(1) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `mail` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `direccion` varchar(100) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `localidad` varchar(60) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `obraSocial` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `plan` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `afiliado` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `telefono` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `celular` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `profesion` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `referente` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci DEFAULT NULL,
  `fechaAlta` date NOT NULL,
  `deBaja` tinyint(1) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idTipoDoc` (`idTipoDoc`,`numDoc`),
  KEY `fechaAlta` (`fechaAlta`)
) ENGINE=MyISAM AUTO_INCREMENT=11565 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `signosvitales`
--

DROP TABLE IF EXISTS `signosvitales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `signosvitales` (
  `idHC` int(10) unsigned NOT NULL,
  `fecha` date NOT NULL,
  `peso` float unsigned DEFAULT NULL,
  `colesterol` float unsigned DEFAULT NULL,
  `glucemia` float unsigned DEFAULT NULL,
  `presionSistolica` int(3) unsigned DEFAULT NULL,
  `presionDiastolica` int(3) unsigned DEFAULT NULL,
  PRIMARY KEY (`idHC`,`fecha`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `stress`
--

DROP TABLE IF EXISTS `stress`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `stress` (
  `idStress` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `idHC` int(10) unsigned NOT NULL,
  `indicacionEstudio` text DEFAULT NULL,
  `tipoApremio` text DEFAULT NULL,
  `medicacionMomentoEstudio` text DEFAULT NULL,
  `medicoSolicitante` text DEFAULT NULL,
  `frecuenciaCardiacaBasal` text DEFAULT NULL,
  `frecuenciaCardiacaMaxima` text DEFAULT NULL,
  `presionArterialBasalInicial` text DEFAULT NULL,
  `presionArterialBasalFinal` text DEFAULT NULL,
  `presionArterialMaximaInicial` text DEFAULT NULL,
  `presionArterialMaximaFinal` text DEFAULT NULL,
  `informeErgometria` text DEFAULT NULL,
  `datosEcocardiograficosBasales` text DEFAULT NULL,
  `datosEcocardiograficosPostEsfuerzoInmediato` text DEFAULT NULL,
  `conclusion` text DEFAULT NULL,
  PRIMARY KEY (`idStress`),
  KEY `idHC` (`idHC`)
) ENGINE=InnoDB AUTO_INCREMENT=108 DEFAULT CHARSET=latin1 COLLATE=latin1_spanish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipo_estudios`
--

DROP TABLE IF EXISTS `tipo_estudios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tipo_estudios` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `pagina` varchar(20) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `orden` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `orden` (`orden`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipocomentario`
--

DROP TABLE IF EXISTS `tipocomentario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tipocomentario` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `descripcion` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=3 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `tipodocumento`
--

DROP TABLE IF EXISTS `tipodocumento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tipodocumento` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `descripcion` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM AUTO_INCREMENT=5 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `pass` varchar(60) CHARACTER SET latin1 COLLATE latin1_spanish_ci NOT NULL,
  `deBaja` tinyint(1) unsigned NOT NULL COMMENT '0=>Activo en el sistema, 1=>Dado de baja en el sistema',
  `idRol` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`),
  KEY `nombre` (`nombre`,`pass`),
  KEY `idRol` (`idRol`)
) ENGINE=MyISAM AUTO_INCREMENT=7 DEFAULT CHARSET=latin1 COLLATE=latin1_swedish_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `view_tipo_estudio`
--

DROP TABLE IF EXISTS `view_tipo_estudio`;
/*!50001 DROP VIEW IF EXISTS `view_tipo_estudio`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `view_tipo_estudio` AS SELECT
 1 AS `id`,
  1 AS `nombre`,
  1 AS `pagina`,
  1 AS `orden` */;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `view_tipo_estudio`
--

/*!50001 DROP VIEW IF EXISTS `view_tipo_estudio`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`u419667151_migration77`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `view_tipo_estudio` AS select `cardioprieto`.`tipo_estudios`.`id` AS `id`,`cardioprieto`.`tipo_estudios`.`nombre` AS `nombre`,`cardioprieto`.`tipo_estudios`.`pagina` AS `pagina`,`cardioprieto`.`tipo_estudios`.`orden` AS `orden` from `tipo_estudios` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2026-04-07  0:21:49
