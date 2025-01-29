CREATE DATABASE  IF NOT EXISTS `trevely` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci */;
USE `trevely`;
-- MySQL dump 10.13  Distrib 8.0.36, for Win64 (x86_64)
--
-- Host: localhost    Database: trevely
-- ------------------------------------------------------
-- Server version	5.5.5-10.4.32-MariaDB

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `adguia`
--

DROP TABLE IF EXISTS `adguia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `adguia` (
  `idAdGuia` int(11) NOT NULL AUTO_INCREMENT,
  `cadastur` varchar(11) DEFAULT NULL,
  `chavePix` varchar(200) DEFAULT NULL,
  `idUsuario` int(11) DEFAULT NULL,
  `calendar_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idAdGuia`),
  KEY `idUsuario` (`idUsuario`),
  CONSTRAINT `adguia_ibfk_1` FOREIGN KEY (`idUsuario`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `adusuario`
--

DROP TABLE IF EXISTS `adusuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `adusuario` (
  `idAdUsuario` int(11) NOT NULL AUTO_INCREMENT,
  `Trabalho` varchar(200) DEFAULT NULL,
  `Lingua` varchar(100) DEFAULT NULL,
  `Descricao` varchar(500) DEFAULT NULL,
  `idUsuario` int(11) DEFAULT NULL,
  PRIMARY KEY (`idAdUsuario`),
  KEY `idUsuario` (`idUsuario`),
  CONSTRAINT `adusuario_ibfk_1` FOREIGN KEY (`idUsuario`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agendamento`
--

DROP TABLE IF EXISTS `agendamento`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `agendamento` (
  `idAgendamento` int(11) NOT NULL AUTO_INCREMENT,
  `qtdMaxTur` int(11) DEFAULT NULL,
  `dataAgendamento` date DEFAULT NULL,
  `horaAgendamento` time DEFAULT NULL,
  `idPasseio` int(11) DEFAULT NULL,
  `idGuiaAg` int(11) DEFAULT NULL,
  `duracaoAgendamento` int(11) DEFAULT NULL,
  `event_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idAgendamento`),
  KEY `idPasseio` (`idPasseio`),
  KEY `idGuiaAg` (`idGuiaAg`),
  CONSTRAINT `agendamento_ibfk_1` FOREIGN KEY (`idPasseio`) REFERENCES `passeio` (`idPasseio`),
  CONSTRAINT `agendamento_ibfk_2` FOREIGN KEY (`idGuiaAg`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=58 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `avaliacaop`
--

DROP TABLE IF EXISTS `avaliacaop`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `avaliacaop` (
  `idAvaliacaoP` int(11) NOT NULL AUTO_INCREMENT,
  `dataAvaliacao` datetime DEFAULT current_timestamp(),
  `descricaoAvaliacao` varchar(500) DEFAULT NULL,
  `idPasseio` int(11) NOT NULL,
  `estrelas` int(11) NOT NULL CHECK (`estrelas` >= 1 and `estrelas` <= 5),
  `usuarioAvaliador` int(11) DEFAULT NULL,
  PRIMARY KEY (`idAvaliacaoP`),
  KEY `idPasseio` (`idPasseio`),
  KEY `fk_usuarioAvaliador` (`usuarioAvaliador`),
  CONSTRAINT `avaliacaop_ibfk_1` FOREIGN KEY (`idPasseio`) REFERENCES `passeio` (`idPasseio`),
  CONSTRAINT `fk_usuarioAvaliador` FOREIGN KEY (`usuarioAvaliador`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=199 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `categoria`
--

DROP TABLE IF EXISTS `categoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categoria` (
  `idCategoria` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`idCategoria`)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `grupopasseios`
--

DROP TABLE IF EXISTS `grupopasseios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `grupopasseios` (
  `idGrupoPasseios` int(11) NOT NULL AUTO_INCREMENT,
  `idAgendamento` int(11) DEFAULT NULL,
  `idTuristaAg` int(11) DEFAULT NULL,
  `idGuiaAg` int(11) DEFAULT NULL,
  `qtdTurGpAgendamento` int(11) DEFAULT NULL,
  `pago` tinyint(1) DEFAULT NULL,
  `vTotal` decimal(10,2) DEFAULT NULL,
  PRIMARY KEY (`idGrupoPasseios`),
  KEY `idAgendamento` (`idAgendamento`),
  KEY `idTuristaAg` (`idTuristaAg`),
  CONSTRAINT `grupopasseios_ibfk_1` FOREIGN KEY (`idAgendamento`) REFERENCES `agendamento` (`idAgendamento`),
  CONSTRAINT `grupopasseios_ibfk_2` FOREIGN KEY (`idTuristaAg`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `imagemusuario`
--

DROP TABLE IF EXISTS `imagemusuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `imagemusuario` (
  `idImagem` int(11) NOT NULL AUTO_INCREMENT,
  `nomeArquivo` varchar(255) DEFAULT NULL,
  `caminhoS3` varchar(255) DEFAULT NULL,
  `idUsuario` int(11) DEFAULT NULL,
  PRIMARY KEY (`idImagem`),
  UNIQUE KEY `idUsuario` (`idUsuario`),
  CONSTRAINT `imagemusuario_ibfk_1` FOREIGN KEY (`idUsuario`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `imagens`
--

DROP TABLE IF EXISTS `imagens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `imagens` (
  `idImagem` int(11) NOT NULL AUTO_INCREMENT,
  `nomeArquivo` varchar(255) DEFAULT NULL,
  `caminhoS3` varchar(255) DEFAULT NULL,
  `idPasseio` int(11) DEFAULT NULL,
  PRIMARY KEY (`idImagem`),
  KEY `idPasseio` (`idPasseio`),
  CONSTRAINT `imagens_ibfk_1` FOREIGN KEY (`idPasseio`) REFERENCES `passeio` (`idPasseio`)
) ENGINE=InnoDB AUTO_INCREMENT=100 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `passeio`
--

DROP TABLE IF EXISTS `passeio`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `passeio` (
  `idPasseio` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(200) DEFAULT NULL,
  `estadoPasseio` varchar(150) DEFAULT NULL,
  `cidadePasseio` varchar(100) DEFAULT NULL,
  `bairroEndPasseio` varchar(200) DEFAULT NULL,
  `valor` double(10,2) DEFAULT NULL,
  `categoria` int(11) DEFAULT NULL,
  `descricaoPasseio` varchar(500) DEFAULT NULL,
  `idGuia` int(11) DEFAULT NULL,
  PRIMARY KEY (`idPasseio`),
  KEY `categoria` (`categoria`),
  KEY `idGuia` (`idGuia`),
  CONSTRAINT `passeio_ibfk_1` FOREIGN KEY (`categoria`) REFERENCES `categoria` (`idCategoria`),
  CONSTRAINT `passeio_ibfk_2` FOREIGN KEY (`idGuia`) REFERENCES `usuario` (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `usuario`
--

DROP TABLE IF EXISTS `usuario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario` (
  `idUsuario` int(11) NOT NULL AUTO_INCREMENT,
  `nome` varchar(200) DEFAULT NULL,
  `cpfCnpj` varchar(14) DEFAULT NULL,
  `numTelefone` varchar(20) DEFAULT NULL,
  `dataNasc` date DEFAULT NULL,
  `cepEndUser` varchar(9) DEFAULT NULL,
  `cidadeUser` varchar(200) DEFAULT NULL,
  `estadoEndUser` varchar(200) DEFAULT NULL,
  `bairroEndUser` varchar(200) DEFAULT NULL,
  `ruaEndUser` varchar(200) DEFAULT NULL,
  `numEndUser` varchar(200) DEFAULT NULL,
  `email` varchar(200) DEFAULT NULL,
  `senha` varchar(200) DEFAULT NULL,
  `tipo` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`idUsuario`)
) ENGINE=InnoDB AUTO_INCREMENT=19 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-12-04 22:16:00
