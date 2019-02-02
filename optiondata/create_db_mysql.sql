-- MySQL dump 10.13  Distrib 5.7.20, for osx10.13 (x86_64)
--
-- Host: localhost    Database: optiondata
-- ------------------------------------------------------
-- Server version	5.7.20

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `fullday`
--

DROP TABLE IF EXISTS `fullday`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `fullday` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `underlying_symbol` varchar(10) DEFAULT NULL,
  `quote_date` date DEFAULT NULL,
  `root` varchar(10) DEFAULT NULL,
  `expiration` date DEFAULT NULL,
  `strike` decimal(10,4) DEFAULT NULL,
  `option_type` char(1) DEFAULT NULL,
  `open` decimal(10,4) DEFAULT NULL,
  `high` decimal(10,4) DEFAULT NULL,
  `low` decimal(10,4) DEFAULT NULL,
  `close` decimal(10,4) DEFAULT NULL,
  `trade_volume` int(11) DEFAULT NULL,
  `bid_size_1545` int(11) DEFAULT NULL,
  `bid_1545` decimal(20,4) DEFAULT NULL,
  `ask_size_1545` int(11) DEFAULT NULL,
  `ask_1545` decimal(20,4) DEFAULT NULL,
  `underlying_bid_1545` decimal(10,4) DEFAULT NULL,
  `underlying_ask_1545` decimal(10,4) DEFAULT NULL,
  `bid_size_eod` int(11) DEFAULT NULL,
  `bid_eod` decimal(20,4) DEFAULT NULL,
  `ask_size_eod` int(11) DEFAULT NULL,
  `ask_eod` decimal(20,4) DEFAULT NULL,
  `underlying_bid_eod` decimal(10,4) DEFAULT NULL,
  `underlying_ask_eod` decimal(10,4) DEFAULT NULL,
  `vwap` text,
  `open_interest` int(11) DEFAULT NULL,
  `delivery_code` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_date` (`quote_date`),
  KEY `idx_expiration` (`expiration`),
  KEY `idx_underlying` (`underlying_symbol`),
  KEY `idx_type` (`option_type`)
) ENGINE=InnoDB AUTO_INCREMENT=916269 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `optiondata`
--

DROP TABLE IF EXISTS `optiondata`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `optiondata` (
  `underlying_symbol` varchar(10) DEFAULT NULL,
  `quote_date` date DEFAULT NULL,
  `root` varchar(10) DEFAULT NULL,
  `expiration` date DEFAULT NULL,
  `strike` decimal(10,4) DEFAULT NULL,
  `option_type` char(1) DEFAULT NULL,
  `open` decimal(10,4) DEFAULT NULL,
  `high` decimal(10,4) DEFAULT NULL,
  `low` decimal(10,4) DEFAULT NULL,
  `close` decimal(10,4) DEFAULT NULL,
  `trade_volume` int(11) DEFAULT NULL,
  `bid_size_1545` int(11) DEFAULT NULL,
  `bid_1545` decimal(20,4) DEFAULT NULL,
  `ask_size_1545` int(11) DEFAULT NULL,
  `ask_1545` decimal(10,4) DEFAULT NULL,
  `underlying_bid_1545` decimal(10,4) DEFAULT NULL,
  `underlying_ask_1545` decimal(10,4) DEFAULT NULL,
  `bid_size_eod` int(11) DEFAULT NULL,
  `bid_eod` decimal(20,4) DEFAULT NULL,
  `ask_size_eod` int(11) DEFAULT NULL,
  `ask_eod` decimal(20,4) DEFAULT NULL,
  `underlying_bid_eod` decimal(10,4) DEFAULT NULL,
  `underlying_ask_eod` decimal(10,4) DEFAULT NULL,
  `vwap` text,
  `open_interest` int(11) DEFAULT NULL,
  `delivery_code` varchar(100) DEFAULT NULL,
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `iv` decimal(65,30) DEFAULT NULL,
  `delta` decimal(65,30) DEFAULT NULL,
  `theta` decimal(65,30) DEFAULT NULL,
  `vega` decimal(65,30) DEFAULT NULL,
  `mid_1545` decimal(20,4) DEFAULT NULL,
  `underlying_mid_1545` decimal(20,4) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_date` (`quote_date`),
  KEY `idx_expiration` (`expiration`),
  KEY `idx_underlying` (`underlying_symbol`),
  KEY `idx_type` (`option_type`),
  KEY `mid_1545` (`mid_1545`)
) ENGINE=InnoDB AUTO_INCREMENT=36355748 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;