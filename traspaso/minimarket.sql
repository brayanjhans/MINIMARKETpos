-- MySQL dump 10.13  Distrib 8.0.45, for Win64 (x86_64)
--
-- Host: localhost    Database: minimarket
-- ------------------------------------------------------
-- Server version	8.0.45

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `abonos`
--

DROP TABLE IF EXISTS `abonos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `abonos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cuenta_por_cobrar_id` int NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `metodo` varchar(30) NOT NULL,
  `referencia` varchar(100) DEFAULT NULL,
  `sesion_caja_id` int DEFAULT NULL,
  `usuario_id` int NOT NULL,
  `fecha` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `fk_abonos_sesion_caja_id_sesiones_caja` (`sesion_caja_id`),
  KEY `fk_abonos_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_abonos_cuenta_por_cobrar_id` (`cuenta_por_cobrar_id`),
  KEY `ix_abonos_fecha` (`fecha`),
  CONSTRAINT `fk_abonos_cuenta_por_cobrar_id_cuentas_por_cobrar` FOREIGN KEY (`cuenta_por_cobrar_id`) REFERENCES `cuentas_por_cobrar` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_abonos_sesion_caja_id_sesiones_caja` FOREIGN KEY (`sesion_caja_id`) REFERENCES `sesiones_caja` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_abonos_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_abonos_monto_positivo` CHECK ((`monto` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `abonos`
--

LOCK TABLES `abonos` WRITE;
/*!40000 ALTER TABLE `abonos` DISABLE KEYS */;
/*!40000 ALTER TABLE `abonos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ajustes_inventario`
--

DROP TABLE IF EXISTS `ajustes_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ajustes_inventario` (
  `id` int NOT NULL AUTO_INCREMENT,
  `numero` varchar(20) NOT NULL,
  `almacen_id` int NOT NULL,
  `motivo_id` int NOT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'BORRADOR',
  `observaciones` varchar(300) DEFAULT NULL,
  `usuario_id` int NOT NULL,
  `aprobado_por_id` int DEFAULT NULL,
  `fecha_aplicacion` datetime DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  `motivo_rechazo` varchar(300) DEFAULT NULL,
  `fecha_envio` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ajustes_inventario_numero` (`numero`),
  KEY `fk_ajustes_inventario_aprobado_por_id_usuarios` (`aprobado_por_id`),
  KEY `fk_ajustes_inventario_motivo_id_motivos_ajuste` (`motivo_id`),
  KEY `fk_ajustes_inventario_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_ajustes_inventario_almacen_estado` (`almacen_id`,`estado`),
  KEY `ix_ajustes_inventario_fecha_aplicacion` (`fecha_aplicacion`),
  CONSTRAINT `fk_ajustes_inventario_almacen_id_almacenes` FOREIGN KEY (`almacen_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ajustes_inventario_aprobado_por_id_usuarios` FOREIGN KEY (`aprobado_por_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ajustes_inventario_motivo_id_motivos_ajuste` FOREIGN KEY (`motivo_id`) REFERENCES `motivos_ajuste` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ajustes_inventario_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ajustes_inventario`
--

LOCK TABLES `ajustes_inventario` WRITE;
/*!40000 ALTER TABLE `ajustes_inventario` DISABLE KEYS */;
INSERT INTO `ajustes_inventario` VALUES (1,'AJ-000001',1,1,'PENDIENTE_APROBACION','Revisión de la mañana: yogurt por vencer en mal estado',1,NULL,NULL,'2026-10-23 16:20:58','2026-10-23 16:20:58',NULL,'2026-10-23 16:20:58');
/*!40000 ALTER TABLE `ajustes_inventario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('ec72af6da32e');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `almacenes`
--

DROP TABLE IF EXISTS `almacenes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `almacenes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sucursal_id` int NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `es_almacen_venta` tinyint(1) NOT NULL DEFAULT '0',
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `sucursal_venta_id` int GENERATED ALWAYS AS ((case when `es_almacen_venta` then `sucursal_id` end)) STORED,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_almacenes_sucursal_id_nombre` (`sucursal_id`,`nombre`),
  UNIQUE KEY `uq_almacenes_sucursal_venta_id` (`sucursal_venta_id`),
  KEY `ix_almacenes_sucursal_id` (`sucursal_id`),
  CONSTRAINT `fk_almacenes_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `almacenes`
--

LOCK TABLES `almacenes` WRITE;
/*!40000 ALTER TABLE `almacenes` DISABLE KEYS */;
INSERT INTO `almacenes` (`id`, `sucursal_id`, `nombre`, `es_almacen_venta`, `activo`, `creado_en`, `actualizado_en`) VALUES (1,1,'Almacén principal',1,1,'2026-10-22 22:00:50','2026-10-22 22:00:50'),(6,1,'Depósito',0,1,'2026-10-23 16:20:57','2026-10-23 16:20:57');
/*!40000 ALTER TABLE `almacenes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `arqueos_denominacion`
--

DROP TABLE IF EXISTS `arqueos_denominacion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `arqueos_denominacion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sesion_caja_id` int NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `denominacion` decimal(12,2) NOT NULL,
  `cantidad` int NOT NULL,
  `subtotal` decimal(12,2) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_arqueos_denominacion_sesion_caja_id_denominacion` (`sesion_caja_id`,`denominacion`),
  CONSTRAINT `fk_arqueos_denominacion_sesion_caja_id_sesiones_caja` FOREIGN KEY (`sesion_caja_id`) REFERENCES `sesiones_caja` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_arqueos_denominacion_cantidad_no_negativa` CHECK ((`cantidad` >= 0)),
  CONSTRAINT `ck_arqueos_denominacion_denominacion_positiva` CHECK ((`denominacion` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `arqueos_denominacion`
--

LOCK TABLES `arqueos_denominacion` WRITE;
/*!40000 ALTER TABLE `arqueos_denominacion` DISABLE KEYS */;
/*!40000 ALTER TABLE `arqueos_denominacion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auditoria`
--

DROP TABLE IF EXISTS `auditoria`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auditoria` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `usuario_id` int DEFAULT NULL,
  `sucursal_id` int DEFAULT NULL,
  `accion` varchar(50) NOT NULL,
  `modulo` varchar(40) NOT NULL,
  `entidad` varchar(60) DEFAULT NULL,
  `entidad_id` varchar(40) DEFAULT NULL,
  `descripcion` varchar(300) DEFAULT NULL,
  `datos` json DEFAULT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `fk_auditoria_sucursal_id_sucursales` (`sucursal_id`),
  KEY `ix_auditoria_creado_en` (`creado_en`),
  KEY `ix_auditoria_modulo_fecha` (`modulo`,`creado_en`),
  KEY `ix_auditoria_usuario_id` (`usuario_id`),
  KEY `ix_auditoria_ip_accion_fecha` (`ip`,`accion`,`creado_en`),
  CONSTRAINT `fk_auditoria_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_auditoria_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=227 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auditoria`
--

LOCK TABLES `auditoria` WRITE;
/*!40000 ALTER TABLE `auditoria` DISABLE KEYS */;
INSERT INTO `auditoria` VALUES (120,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-22 23:11:26'),(121,1,NULL,'LOGIN_FALLIDO','auth','usuario','1','Contraseña incorrecta (intento 1)','null','127.0.0.1','2026-10-22 23:11:27'),(122,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:14:20'),(123,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:14:23'),(124,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:14:26'),(125,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:14:30'),(126,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:14:36'),(127,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:14:39'),(128,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:14:42'),(129,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:14:45'),(130,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:16:14'),(131,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:16:17'),(132,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:16:20'),(133,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:16:26'),(134,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:16:29'),(135,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:16:32'),(136,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:17:18'),(137,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:17:21'),(138,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:18:26'),(139,1,1,'LOGOUT','auth',NULL,NULL,'Cierre de sesión','null','127.0.0.1','2026-10-23 14:18:26'),(140,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:18:26'),(141,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 14:59:25'),(142,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 15:21:04'),(143,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 15:23:31'),(144,1,1,'LOGOUT','auth',NULL,NULL,'Cierre de sesión','null','127.0.0.1','2026-10-23 15:23:31'),(145,1,1,'CREAR','productos','producto','3','Creó el producto Arroz Costeño extra 1 kg','{\"codigos\": [\"2000000010014\"], \"precio_venta\": \"4.50\"}','127.0.0.1','2026-10-23 16:20:57'),(146,1,1,'CREAR','productos','producto','4','Creó el producto Azúcar rubia Dulfina 1 kg','{\"codigos\": [\"2000000010021\"], \"precio_venta\": \"3.80\"}','127.0.0.1','2026-10-23 16:20:57'),(147,1,1,'CREAR','productos','producto','5','Creó el producto Aceite Primor premium 1 L','{\"codigos\": [\"2000000010038\"], \"precio_venta\": \"11.50\"}','127.0.0.1','2026-10-23 16:20:57'),(148,1,1,'CREAR','productos','producto','6','Creó el producto Fideo spaghetti Don Vittorio 500 g','{\"codigos\": [\"2000000010045\"], \"precio_venta\": \"3.60\"}','127.0.0.1','2026-10-23 16:20:57'),(149,1,1,'CREAR','productos','producto','7','Creó el producto Atún Florida filete 170 g','{\"codigos\": [\"2000000010052\"], \"precio_venta\": \"6.90\"}','127.0.0.1','2026-10-23 16:20:57'),(150,1,1,'CREAR','productos','producto','8','Creó el producto Leche Gloria evaporada 400 g','{\"codigos\": [\"2000000010069\"], \"precio_venta\": \"4.20\"}','127.0.0.1','2026-10-23 16:20:57'),(151,1,1,'CREAR','productos','producto','9','Creó el producto Gaseosa Inca Kola 1.5 L','{\"codigos\": [\"2000000010076\"], \"precio_venta\": \"7.50\"}','127.0.0.1','2026-10-23 16:20:57'),(152,1,1,'CREAR','productos','producto','10','Creó el producto Gaseosa Coca-Cola 500 ml','{\"codigos\": [\"2000000010083\"], \"precio_venta\": \"3.00\"}','127.0.0.1','2026-10-23 16:20:57'),(153,1,1,'CREAR','productos','producto','11','Creó el producto Agua San Luis sin gas 625 ml','{\"codigos\": [\"2000000010090\"], \"precio_venta\": \"1.80\"}','127.0.0.1','2026-10-23 16:20:57'),(154,1,1,'CREAR','productos','producto','12','Creó el producto Gaseosa Guaraná 1 L','{\"codigos\": [\"2000000010106\"], \"precio_venta\": \"4.00\"}','127.0.0.1','2026-10-23 16:20:57'),(155,1,1,'CREAR','productos','producto','13','Creó el producto Frugos del Valle durazno 1 L','{\"codigos\": [\"2000000010113\"], \"precio_venta\": \"4.50\"}','127.0.0.1','2026-10-23 16:20:57'),(156,1,1,'CREAR','productos','producto','14','Creó el producto Red Bull 250 ml','{\"codigos\": [\"2000000010120\"], \"precio_venta\": \"7.50\"}','127.0.0.1','2026-10-23 16:20:57'),(157,1,1,'CREAR','productos','producto','15','Creó el producto Cerveza Pilsen Callao 630 ml','{\"codigos\": [\"2000000010137\"], \"precio_venta\": \"6.50\"}','127.0.0.1','2026-10-23 16:20:57'),(158,1,1,'CREAR','productos','producto','16','Creó el producto Cerveza Cusqueña dorada lata 355 ml','{\"codigos\": [\"2000000010144\"], \"precio_venta\": \"4.50\"}','127.0.0.1','2026-10-23 16:20:57'),(159,1,1,'CREAR','productos','producto','17','Creó el producto Yogurt Gloria fresa 1 L','{\"codigos\": [\"2000000010151\"], \"precio_venta\": \"6.90\"}','127.0.0.1','2026-10-23 16:20:57'),(160,1,1,'CREAR','productos','producto','18','Creó el producto Queso fresco Laive 500 g','{\"codigos\": [\"2000000010168\"], \"precio_venta\": \"17.90\"}','127.0.0.1','2026-10-23 16:20:57'),(161,1,1,'CREAR','productos','producto','19','Creó el producto Mantequilla Laive con sal 200 g','{\"codigos\": [\"2000000010175\"], \"precio_venta\": \"9.20\"}','127.0.0.1','2026-10-23 16:20:57'),(162,1,1,'CREAR','productos','producto','20','Creó el producto Huevos rosados (unidad)','{\"codigos\": [\"2000000010182\"], \"precio_venta\": \"0.60\"}','127.0.0.1','2026-10-23 16:20:57'),(163,1,1,'CREAR','productos','producto','21','Creó el producto Pan francés','{\"codigos\": [], \"precio_venta\": \"0.20\"}','127.0.0.1','2026-10-23 16:20:57'),(164,1,1,'CREAR','productos','producto','22','Creó el producto Pan de molde Bimbo blanco','{\"codigos\": [\"2000000010205\"], \"precio_venta\": \"8.90\"}','127.0.0.1','2026-10-23 16:20:57'),(165,1,1,'CREAR','productos','producto','23','Creó el producto Galletas Soda Field paquete x6','{\"codigos\": [\"2000000010212\"], \"precio_venta\": \"3.20\"}','127.0.0.1','2026-10-23 16:20:57'),(166,1,1,'CREAR','productos','producto','24','Creó el producto Papas Lay\'s clásicas 42 g','{\"codigos\": [\"2000000010229\"], \"precio_venta\": \"2.50\"}','127.0.0.1','2026-10-23 16:20:57'),(167,1,1,'CREAR','productos','producto','25','Creó el producto Chocolate Sublime clásico 30 g','{\"codigos\": [\"2000000010236\"], \"precio_venta\": \"1.50\"}','127.0.0.1','2026-10-23 16:20:57'),(168,1,1,'CREAR','productos','producto','26','Creó el producto Galletas Oreo 36 g','{\"codigos\": [\"2000000010243\"], \"precio_venta\": \"1.20\"}','127.0.0.1','2026-10-23 16:20:57'),(169,1,1,'CREAR','productos','producto','27','Creó el producto Detergente Bolívar 750 g','{\"codigos\": [\"2000000010250\"], \"precio_venta\": \"9.90\"}','127.0.0.1','2026-10-23 16:20:57'),(170,1,1,'CREAR','productos','producto','28','Creó el producto Lejía Clorox 1 L','{\"codigos\": [\"2000000010267\"], \"precio_venta\": \"4.20\"}','127.0.0.1','2026-10-23 16:20:57'),(171,1,1,'CREAR','productos','producto','29','Creó el producto Lavavajilla Ayudín limón 450 g','{\"codigos\": [\"2000000010274\"], \"precio_venta\": \"5.50\"}','127.0.0.1','2026-10-23 16:20:57'),(172,1,1,'CREAR','productos','producto','30','Creó el producto Papel higiénico Elite x4','{\"codigos\": [\"2000000010281\"], \"precio_venta\": \"6.90\"}','127.0.0.1','2026-10-23 16:20:57'),(173,1,1,'CREAR','productos','producto','31','Creó el producto Jabón Protex avena 110 g','{\"codigos\": [\"2000000010298\"], \"precio_venta\": \"3.90\"}','127.0.0.1','2026-10-23 16:20:58'),(174,1,1,'CREAR','productos','producto','32','Creó el producto Pasta dental Colgate triple acción 75 ml','{\"codigos\": [\"2000000010304\"], \"precio_venta\": \"5.90\"}','127.0.0.1','2026-10-23 16:20:58'),(175,1,1,'CREAR','productos','producto','33','Creó el producto Plátano de seda','{\"codigos\": [], \"precio_venta\": \"3.50\"}','127.0.0.1','2026-10-23 16:20:58'),(176,1,1,'CREAR','productos','producto','34','Creó el producto Papa amarilla','{\"codigos\": [], \"precio_venta\": \"4.20\"}','127.0.0.1','2026-10-23 16:20:58'),(177,1,1,'CREAR','productos','producto','35','Creó el producto Limón','{\"codigos\": [], \"precio_venta\": \"6.00\"}','127.0.0.1','2026-10-23 16:20:58'),(178,1,1,'CREAR','productos','producto','36','Creó el producto Hot dog San Fernando x10','{\"codigos\": [\"2000000010342\"], \"precio_venta\": \"8.50\"}','127.0.0.1','2026-10-23 16:20:58'),(179,1,1,'STOCK_INICIAL','inventario','almacen','1','Cargó stock inicial de 32 producto(s) en Almacén principal','{\"valor\": \"3162.68\", \"unidades\": \"1117.50\", \"productos\": \"32\"}','127.0.0.1','2026-10-23 16:20:58'),(180,1,1,'CREAR','inventario','ajuste','1','Registró el ajuste AJ-000001 (Producto vencido) y lo envió a aprobación','null','127.0.0.1','2026-10-23 16:20:58'),(181,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 16:21:12'),(182,1,1,'REVISAR_INTEGRIDAD','inventario',NULL,NULL,'Revisión de integridad del stock: sin problemas','null','127.0.0.1','2026-10-23 16:21:12'),(183,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 16:27:11'),(184,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 16:27:14'),(185,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 16:28:47'),(186,1,1,'EDITAR','productos','producto','16','Editó el producto Cerveza Cusqueña dorada lata 355 ml','{\"campos\": [\"precio_costo\"]}','127.0.0.1','2026-10-23 16:28:48'),(187,1,1,'EDITAR','productos','producto','26','Editó el producto Galletas Oreo 36 g','{\"campos\": [\"precio_costo\"]}','127.0.0.1','2026-10-23 16:28:48'),(188,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:12'),(189,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:15'),(190,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:18'),(191,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:21'),(192,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:24'),(193,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:28'),(194,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:31'),(195,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:34'),(196,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:38'),(197,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:29:41'),(198,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:30:51'),(199,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:31:38'),(200,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:31:41'),(201,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:31:44'),(202,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:32:30'),(203,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:34:05'),(204,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 20:34:09'),(205,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:28:16'),(206,1,1,'ABRIR','caja','sesion_caja','5','Abrió la Caja 1 con S/ 100.00','{\"monto_inicial\": \"100.00\"}','127.0.0.1','2026-10-23 22:28:16'),(207,1,1,'REVISAR_INTEGRIDAD','inventario',NULL,NULL,'Revisión de integridad del stock: sin problemas','null','127.0.0.1','2026-10-23 22:28:16'),(208,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:28:23'),(209,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:28:28'),(210,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:28:34'),(211,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:28:38'),(212,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:28:42'),(213,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:28:46'),(214,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:28:51'),(215,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:30:08'),(216,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:31:32'),(217,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:32:18'),(218,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:36:47'),(219,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:39:27'),(220,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:39:31'),(221,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:39:34'),(222,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:39:37'),(223,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:41:00'),(224,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:42:04'),(225,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:48:59'),(226,1,1,'LOGIN','auth',NULL,NULL,'Inicio de sesión','null','127.0.0.1','2026-10-23 22:49:02');
/*!40000 ALTER TABLE `auditoria` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cajas`
--

DROP TABLE IF EXISTS `cajas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cajas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sucursal_id` int NOT NULL,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cajas_sucursal_id_nombre` (`sucursal_id`,`nombre`),
  KEY `ix_cajas_sucursal_id` (`sucursal_id`),
  CONSTRAINT `fk_cajas_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cajas`
--

LOCK TABLES `cajas` WRITE;
/*!40000 ALTER TABLE `cajas` DISABLE KEYS */;
INSERT INTO `cajas` VALUES (1,1,'Caja 1','Caja principal',1,'2026-10-22 22:00:50','2026-10-22 22:00:50');
/*!40000 ALTER TABLE `cajas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categorias`
--

DROP TABLE IF EXISTS `categorias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categorias` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `descripcion` varchar(250) DEFAULT NULL,
  `color` varchar(7) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_categorias_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categorias`
--

LOCK TABLES `categorias` WRITE;
/*!40000 ALTER TABLE `categorias` DISABLE KEYS */;
INSERT INTO `categorias` VALUES (1,'Abarrotes','Arroz, azúcar, aceite, fideos, menestras','#f59e0b',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(2,'Bebidas','Gaseosas, aguas, jugos, energizantes','#3b82f6',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(3,'Lácteos y huevos','Leche, yogurt, quesos, mantequilla, huevos','#facc15',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(4,'Panadería','Pan, galletas, queques','#d97706',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(5,'Snacks y golosinas','Papitas, chocolates, caramelos','#ec4899',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(6,'Limpieza','Detergentes, lejía, desinfectantes','#06b6d4',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(7,'Cuidado personal','Jabón, champú, papel higiénico, pasta dental','#8b5cf6',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(8,'Licores','Cervezas, vinos, licores','#ef4444',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(9,'Embutidos y carnes','Jamón, hot dog, pollo, carnes','#f97316',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(10,'Frutas y verduras','Productos frescos a granel','#22c55e',1,'2026-10-22 22:00:51','2026-10-22 22:00:51');
/*!40000 ALTER TABLE `categorias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `clientes`
--

DROP TABLE IF EXISTS `clientes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `clientes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `tipo_documento` varchar(30) NOT NULL,
  `numero_documento` varchar(15) DEFAULT NULL,
  `nombre` varchar(200) NOT NULL,
  `direccion` varchar(250) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `permite_credito` tinyint(1) NOT NULL DEFAULT '0',
  `limite_credito` decimal(12,2) NOT NULL DEFAULT '0.00',
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_clientes_tipo_documento_numero_documento` (`tipo_documento`,`numero_documento`),
  KEY `ix_clientes_numero_documento` (`numero_documento`),
  FULLTEXT KEY `ftx_clientes_nombre` (`nombre`) /*!50100 WITH PARSER `ngram` */ ,
  CONSTRAINT `ck_clientes_limite_credito_no_negativo` CHECK ((`limite_credito` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `clientes`
--

LOCK TABLES `clientes` WRITE;
/*!40000 ALTER TABLE `clientes` DISABLE KEYS */;
/*!40000 ALTER TABLE `clientes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `codigos_barras`
--

DROP TABLE IF EXISTS `codigos_barras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `codigos_barras` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(50) NOT NULL,
  `producto_id` int NOT NULL,
  `presentacion_id` int DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_codigos_barras_codigo` (`codigo`),
  KEY `ix_codigos_barras_presentacion_id` (`presentacion_id`),
  KEY `ix_codigos_barras_producto_id` (`producto_id`),
  CONSTRAINT `fk_codigos_barras_presentacion_id_producto_presentaciones` FOREIGN KEY (`presentacion_id`) REFERENCES `producto_presentaciones` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_codigos_barras_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `codigos_barras`
--

LOCK TABLES `codigos_barras` WRITE;
/*!40000 ALTER TABLE `codigos_barras` DISABLE KEYS */;
INSERT INTO `codigos_barras` VALUES (1,'2000000010014',3,NULL,'2026-10-23 16:20:57'),(2,'2000000010021',4,NULL,'2026-10-23 16:20:57'),(3,'2000000010038',5,NULL,'2026-10-23 16:20:57'),(4,'2000000010045',6,NULL,'2026-10-23 16:20:57'),(5,'2000000010052',7,NULL,'2026-10-23 16:20:57'),(6,'2000000010069',8,NULL,'2026-10-23 16:20:57'),(7,'2000000010076',9,NULL,'2026-10-23 16:20:57'),(8,'2000000090085',10,3,'2026-10-23 16:20:57'),(9,'2000000010083',10,NULL,'2026-10-23 16:20:57'),(10,'2000000010090',11,NULL,'2026-10-23 16:20:57'),(11,'2000000010106',12,NULL,'2026-10-23 16:20:57'),(12,'2000000010113',13,NULL,'2026-10-23 16:20:57'),(13,'2000000010120',14,NULL,'2026-10-23 16:20:57'),(14,'2000000090139',15,4,'2026-10-23 16:20:57'),(15,'2000000010137',15,NULL,'2026-10-23 16:20:57'),(16,'2000000010144',16,NULL,'2026-10-23 16:20:57'),(17,'2000000010151',17,NULL,'2026-10-23 16:20:57'),(18,'2000000010168',18,NULL,'2026-10-23 16:20:57'),(19,'2000000010175',19,NULL,'2026-10-23 16:20:57'),(20,'2000000010182',20,NULL,'2026-10-23 16:20:57'),(21,'2000000010205',22,NULL,'2026-10-23 16:20:57'),(22,'2000000010212',23,NULL,'2026-10-23 16:20:57'),(23,'2000000010229',24,NULL,'2026-10-23 16:20:57'),(24,'2000000090238',25,5,'2026-10-23 16:20:57'),(25,'2000000010236',25,NULL,'2026-10-23 16:20:57'),(26,'2000000010243',26,NULL,'2026-10-23 16:20:57'),(27,'2000000010250',27,NULL,'2026-10-23 16:20:57'),(28,'2000000010267',28,NULL,'2026-10-23 16:20:57'),(29,'2000000010274',29,NULL,'2026-10-23 16:20:57'),(30,'2000000010281',30,NULL,'2026-10-23 16:20:57'),(31,'2000000010298',31,NULL,'2026-10-23 16:20:58'),(32,'2000000010304',32,NULL,'2026-10-23 16:20:58'),(33,'2000000010342',36,NULL,'2026-10-23 16:20:58');
/*!40000 ALTER TABLE `codigos_barras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `compras`
--

DROP TABLE IF EXISTS `compras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compras` (
  `id` int NOT NULL AUTO_INCREMENT,
  `numero` varchar(20) NOT NULL,
  `proveedor_id` int NOT NULL,
  `almacen_id` int NOT NULL,
  `usuario_id` int NOT NULL,
  `tipo_documento` varchar(20) DEFAULT NULL,
  `numero_documento` varchar(30) DEFAULT NULL,
  `fecha_emision` date NOT NULL,
  `fecha_recepcion` datetime DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'PENDIENTE',
  `condicion_pago` varchar(30) NOT NULL DEFAULT 'CONTADO',
  `subtotal` decimal(12,2) NOT NULL DEFAULT '0.00',
  `igv` decimal(12,2) NOT NULL DEFAULT '0.00',
  `total` decimal(12,2) NOT NULL DEFAULT '0.00',
  `observaciones` varchar(300) DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_compras_numero` (`numero`),
  KEY `fk_compras_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_compras_almacen_id` (`almacen_id`),
  KEY `ix_compras_estado` (`estado`),
  KEY `ix_compras_fecha_emision` (`fecha_emision`),
  KEY `ix_compras_fecha_recepcion` (`fecha_recepcion`),
  KEY `ix_compras_proveedor_fecha` (`proveedor_id`,`fecha_emision`),
  CONSTRAINT `fk_compras_almacen_id_almacenes` FOREIGN KEY (`almacen_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_compras_proveedor_id_proveedores` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_compras_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_compras_total_no_negativo` CHECK ((`total` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compras`
--

LOCK TABLES `compras` WRITE;
/*!40000 ALTER TABLE `compras` DISABLE KEYS */;
/*!40000 ALTER TABLE `compras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `correlativos`
--

DROP TABLE IF EXISTS `correlativos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `correlativos` (
  `clave` varchar(30) NOT NULL,
  `prefijo` varchar(5) NOT NULL,
  `ultimo_numero` int NOT NULL DEFAULT '0',
  `longitud` int NOT NULL DEFAULT '6',
  `descripcion` varchar(100) NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`clave`),
  CONSTRAINT `ck_correlativos_ultimo_numero_no_negativo` CHECK ((`ultimo_numero` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `correlativos`
--

LOCK TABLES `correlativos` WRITE;
/*!40000 ALTER TABLE `correlativos` DISABLE KEYS */;
INSERT INTO `correlativos` VALUES ('AJUSTE','AJ',1,6,'Ajustes de inventario','2026-10-22 22:00:51','2026-10-23 16:20:58'),('DEVOLUCION','DV',0,6,'Devoluciones de ventas','2026-10-22 22:00:51','2026-10-22 22:00:51'),('INVENTARIO_FISICO','IF',0,6,'Inventarios físicos','2026-10-22 22:00:51','2026-10-22 22:00:51'),('ORDEN_COMPRA','OC',0,6,'Órdenes de compra','2026-10-22 22:00:51','2026-10-22 22:00:51'),('TRANSFERENCIA','TR',0,6,'Transferencias entre almacenes','2026-10-22 22:00:51','2026-10-22 22:00:51');
/*!40000 ALTER TABLE `correlativos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cuentas_por_cobrar`
--

DROP TABLE IF EXISTS `cuentas_por_cobrar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cuentas_por_cobrar` (
  `id` int NOT NULL AUTO_INCREMENT,
  `venta_id` bigint NOT NULL,
  `cliente_id` int NOT NULL,
  `monto_total` decimal(12,2) NOT NULL,
  `saldo` decimal(12,2) NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'PENDIENTE',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cuentas_por_cobrar_venta_id` (`venta_id`),
  KEY `ix_cuentas_por_cobrar_cliente_id` (`cliente_id`),
  KEY `ix_cuentas_por_cobrar_estado` (`estado`),
  KEY `ix_cuentas_por_cobrar_fecha_vencimiento` (`fecha_vencimiento`),
  CONSTRAINT `fk_cuentas_por_cobrar_cliente_id_clientes` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_cuentas_por_cobrar_venta_id_ventas` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_cuentas_por_cobrar_saldo_no_excede_total` CHECK ((`saldo` <= `monto_total`)),
  CONSTRAINT `ck_cuentas_por_cobrar_saldo_no_negativo` CHECK ((`saldo` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cuentas_por_cobrar`
--

LOCK TABLES `cuentas_por_cobrar` WRITE;
/*!40000 ALTER TABLE `cuentas_por_cobrar` DISABLE KEYS */;
/*!40000 ALTER TABLE `cuentas_por_cobrar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `cuentas_por_pagar`
--

DROP TABLE IF EXISTS `cuentas_por_pagar`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cuentas_por_pagar` (
  `id` int NOT NULL AUTO_INCREMENT,
  `compra_id` int NOT NULL,
  `proveedor_id` int NOT NULL,
  `monto_total` decimal(12,2) NOT NULL,
  `saldo` decimal(12,2) NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'PENDIENTE',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cuentas_por_pagar_compra_id` (`compra_id`),
  KEY `ix_cuentas_por_pagar_estado` (`estado`),
  KEY `ix_cuentas_por_pagar_fecha_vencimiento` (`fecha_vencimiento`),
  KEY `ix_cuentas_por_pagar_proveedor_id` (`proveedor_id`),
  CONSTRAINT `fk_cuentas_por_pagar_compra_id_compras` FOREIGN KEY (`compra_id`) REFERENCES `compras` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_cuentas_por_pagar_proveedor_id_proveedores` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_cuentas_por_pagar_saldo_no_excede_total` CHECK ((`saldo` <= `monto_total`)),
  CONSTRAINT `ck_cuentas_por_pagar_saldo_no_negativo` CHECK ((`saldo` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `cuentas_por_pagar`
--

LOCK TABLES `cuentas_por_pagar` WRITE;
/*!40000 ALTER TABLE `cuentas_por_pagar` DISABLE KEYS */;
/*!40000 ALTER TABLE `cuentas_por_pagar` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalles_ajuste_inventario`
--

DROP TABLE IF EXISTS `detalles_ajuste_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalles_ajuste_inventario` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ajuste_id` int NOT NULL,
  `producto_id` int NOT NULL,
  `lote_id` int DEFAULT NULL,
  `cantidad` decimal(12,3) NOT NULL,
  `costo_unitario` decimal(14,4) NOT NULL,
  `numero_lote` varchar(50) DEFAULT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_detalles_ajuste_inventario_lote_id_lotes` (`lote_id`),
  KEY `ix_detalles_ajuste_inventario_ajuste_id` (`ajuste_id`),
  KEY `ix_detalles_ajuste_inventario_producto_id` (`producto_id`),
  CONSTRAINT `fk_detalles_ajuste_inventario_ajuste_id_ajustes_inventario` FOREIGN KEY (`ajuste_id`) REFERENCES `ajustes_inventario` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_detalles_ajuste_inventario_lote_id_lotes` FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_detalles_ajuste_inventario_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_detalles_ajuste_inventario_cantidad_no_cero` CHECK ((`cantidad` <> 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalles_ajuste_inventario`
--

LOCK TABLES `detalles_ajuste_inventario` WRITE;
/*!40000 ALTER TABLE `detalles_ajuste_inventario` DISABLE KEYS */;
INSERT INTO `detalles_ajuste_inventario` VALUES (1,1,17,3,-2.000,5.1000,NULL,NULL);
/*!40000 ALTER TABLE `detalles_ajuste_inventario` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalles_compra`
--

DROP TABLE IF EXISTS `detalles_compra`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalles_compra` (
  `id` int NOT NULL AUTO_INCREMENT,
  `compra_id` int NOT NULL,
  `producto_id` int NOT NULL,
  `cantidad` decimal(12,3) NOT NULL,
  `cantidad_recibida` decimal(12,3) NOT NULL DEFAULT '0.000',
  `costo_unitario` decimal(14,4) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `numero_lote` varchar(50) DEFAULT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_detalles_compra_compra_id` (`compra_id`),
  KEY `ix_detalles_compra_producto_id` (`producto_id`),
  CONSTRAINT `fk_detalles_compra_compra_id_compras` FOREIGN KEY (`compra_id`) REFERENCES `compras` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_detalles_compra_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_detalles_compra_cantidad_positiva` CHECK ((`cantidad` > 0)),
  CONSTRAINT `ck_detalles_compra_cantidad_recibida_no_negativa` CHECK ((`cantidad_recibida` >= 0)),
  CONSTRAINT `ck_detalles_compra_costo_no_negativo` CHECK ((`costo_unitario` >= 0)),
  CONSTRAINT `ck_detalles_compra_recibida_no_excede` CHECK ((`cantidad_recibida` <= `cantidad`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalles_compra`
--

LOCK TABLES `detalles_compra` WRITE;
/*!40000 ALTER TABLE `detalles_compra` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalles_compra` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalles_devolucion`
--

DROP TABLE IF EXISTS `detalles_devolucion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalles_devolucion` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `devolucion_id` bigint NOT NULL,
  `detalle_venta_id` bigint NOT NULL,
  `producto_id` int NOT NULL,
  `cantidad` decimal(12,3) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `reingresa_stock` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  KEY `fk_detalles_devolucion_producto_id_productos` (`producto_id`),
  KEY `ix_detalles_devolucion_detalle_venta_id` (`detalle_venta_id`),
  KEY `ix_detalles_devolucion_devolucion_id` (`devolucion_id`),
  CONSTRAINT `fk_detalles_devolucion_detalle_venta_id_detalles_venta` FOREIGN KEY (`detalle_venta_id`) REFERENCES `detalles_venta` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_detalles_devolucion_devolucion_id_devoluciones` FOREIGN KEY (`devolucion_id`) REFERENCES `devoluciones` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_detalles_devolucion_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_detalles_devolucion_cantidad_positiva` CHECK ((`cantidad` > 0)),
  CONSTRAINT `ck_detalles_devolucion_total_no_negativo` CHECK ((`total` >= 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalles_devolucion`
--

LOCK TABLES `detalles_devolucion` WRITE;
/*!40000 ALTER TABLE `detalles_devolucion` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalles_devolucion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalles_inventario_fisico`
--

DROP TABLE IF EXISTS `detalles_inventario_fisico`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalles_inventario_fisico` (
  `id` int NOT NULL AUTO_INCREMENT,
  `inventario_id` int NOT NULL,
  `producto_id` int NOT NULL,
  `stock_sistema` decimal(12,3) NOT NULL,
  `stock_contado` decimal(12,3) DEFAULT NULL,
  `diferencia` decimal(12,3) DEFAULT NULL,
  `lote_id` int DEFAULT NULL,
  `lote_clave` int GENERATED ALWAYS AS (coalesce(`lote_id`,0)) STORED NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_detalles_inventario_fisico_inventario_id_producto_id__3feb` (`inventario_id`,`producto_id`,`lote_clave`),
  KEY `ix_detalles_inventario_fisico_inventario_id` (`inventario_id`),
  KEY `ix_detalles_inventario_fisico_producto_id` (`producto_id`),
  KEY `fk_detalles_inventario_fisico_lote_id_lotes` (`lote_id`),
  CONSTRAINT `fk_detalles_inventario_fisico_inventario_id_inventarios_fisicos` FOREIGN KEY (`inventario_id`) REFERENCES `inventarios_fisicos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_detalles_inventario_fisico_lote_id_lotes` FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_detalles_inventario_fisico_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalles_inventario_fisico`
--

LOCK TABLES `detalles_inventario_fisico` WRITE;
/*!40000 ALTER TABLE `detalles_inventario_fisico` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalles_inventario_fisico` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalles_transferencia`
--

DROP TABLE IF EXISTS `detalles_transferencia`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalles_transferencia` (
  `id` int NOT NULL AUTO_INCREMENT,
  `transferencia_id` int NOT NULL,
  `producto_id` int NOT NULL,
  `lote_id` int DEFAULT NULL,
  `cantidad` decimal(12,3) NOT NULL,
  `cantidad_recibida` decimal(12,3) NOT NULL DEFAULT '0.000',
  `costo_unitario` decimal(14,4) NOT NULL DEFAULT '0.0000',
  `motivo_faltante` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_detalles_transferencia_lote_id_lotes` (`lote_id`),
  KEY `ix_detalles_transferencia_producto_id` (`producto_id`),
  KEY `ix_detalles_transferencia_transferencia_id` (`transferencia_id`),
  CONSTRAINT `fk_detalles_transferencia_lote_id_lotes` FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_detalles_transferencia_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_detalles_transferencia_transferencia_id_transferencias` FOREIGN KEY (`transferencia_id`) REFERENCES `transferencias` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_detalles_transferencia_cantidad_positiva` CHECK ((`cantidad` > 0)),
  CONSTRAINT `ck_detalles_transferencia_cantidad_recibida_no_negativa` CHECK ((`cantidad_recibida` >= 0)),
  CONSTRAINT `ck_detalles_transferencia_recibida_no_excede` CHECK ((`cantidad_recibida` <= `cantidad`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalles_transferencia`
--

LOCK TABLES `detalles_transferencia` WRITE;
/*!40000 ALTER TABLE `detalles_transferencia` DISABLE KEYS */;
/*!40000 ALTER TABLE `detalles_transferencia` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `detalles_venta`
--

DROP TABLE IF EXISTS `detalles_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalles_venta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `venta_id` bigint NOT NULL,
  `producto_id` int NOT NULL,
  `presentacion_id` int DEFAULT NULL,
  `descripcion` varchar(200) NOT NULL,
  `cantidad` decimal(12,3) NOT NULL,
  `factor` decimal(12,3) NOT NULL DEFAULT '1.000',
  `precio_unitario` decimal(12,2) NOT NULL,
  `costo_unitario` decimal(14,4) NOT NULL,
  `descuento` decimal(12,2) NOT NULL DEFAULT '0.00',
  `tipo_afectacion_igv` varchar(30) NOT NULL,
  `igv` decimal(12,2) NOT NULL DEFAULT '0.00',
  `icbper` decimal(12,2) NOT NULL DEFAULT '0.00',
  `total` decimal(12,2) NOT NULL,
  `cantidad_devuelta` decimal(12,3) NOT NULL DEFAULT '0.000',
  PRIMARY KEY (`id`),
  KEY `fk_detalles_venta_presentacion_id_producto_presentaciones` (`presentacion_id`),
  KEY `ix_detalles_venta_producto_id` (`producto_id`),
  KEY `ix_detalles_venta_venta_id` (`venta_id`),
  CONSTRAINT `fk_detalles_venta_presentacion_id_producto_presentaciones` FOREIGN KEY (`presentacion_id`) REFERENCES `producto_presentaciones` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_detalles_venta_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_detalles_venta_venta_id_ventas` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_detalles_venta_cantidad_positiva` CHECK ((`cantidad` > 0)),
  CONSTRAINT `ck_detalles_venta_descuento_no_negativo` CHECK ((`descuento` >= 0)),
  CONSTRAINT `ck_detalles_venta_devuelta_valida` CHECK (((`cantidad_devuelta` >= 0) and (`cantidad_devuelta` <= `cantidad`))),
  CONSTRAINT `ck_detalles_venta_factor_positivo` CHECK ((`factor` > 0)),
  CONSTRAINT `ck_detalles_venta_precio_unitario_no_negativo` CHECK ((`precio_unitario` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `detalles_venta`
--

LOCK TABLES `detalles_venta` WRITE;
/*!40000 ALTER TABLE `detalles_venta` DISABLE KEYS */;
INSERT INTO `detalles_venta` VALUES (3,3,11,NULL,'Agua San Luis sin gas 625 ml',2.000,1.000,1.80,1.1000,0.00,'GRAVADO',0.55,0.00,3.60,0.000),(4,3,3,NULL,'Arroz Costeño extra 1 kg',1.000,1.000,4.50,3.9500,0.00,'GRAVADO',0.69,0.00,4.50,0.000),(5,4,7,NULL,'Atún Florida filete 170 g',3.000,1.000,6.90,5.3000,0.00,'GRAVADO',3.16,0.00,20.70,0.000),(6,5,15,NULL,'Cerveza Pilsen Callao 630 ml',1.000,1.000,6.50,4.9000,0.00,'GRAVADO',0.99,0.00,6.50,0.000),(7,5,25,NULL,'Chocolate Sublime clásico 30 g',2.000,1.000,1.50,1.0500,0.00,'GRAVADO',0.46,0.00,3.00,0.000),(8,6,11,NULL,'Agua San Luis sin gas 625 ml',2.000,1.000,1.80,1.1000,0.00,'GRAVADO',0.55,0.00,3.60,0.000),(9,6,3,NULL,'Arroz Costeño extra 1 kg',1.000,1.000,4.50,3.9500,0.00,'GRAVADO',0.69,0.00,4.50,0.000),(10,6,33,NULL,'Plátano de seda',1.250,1.000,3.50,2.4000,0.00,'EXONERADO',0.00,0.00,4.38,0.000),(11,6,25,NULL,'Chocolate Sublime clásico 30 g',1.000,1.000,1.50,1.0500,0.00,'GRAVADO',0.23,0.00,1.50,0.000),(12,6,27,NULL,'Detergente Bolívar 750 g',2.000,1.000,9.90,7.8000,0.00,'GRAVADO',3.02,0.00,19.80,0.000);
/*!40000 ALTER TABLE `detalles_venta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `devoluciones`
--

DROP TABLE IF EXISTS `devoluciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `devoluciones` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `numero` varchar(20) NOT NULL,
  `venta_id` bigint NOT NULL,
  `sucursal_id` int NOT NULL,
  `sesion_caja_id` int DEFAULT NULL,
  `metodo_reembolso` varchar(30) NOT NULL,
  `total` decimal(12,2) NOT NULL,
  `motivo` varchar(300) NOT NULL,
  `usuario_id` int NOT NULL,
  `fecha` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_devoluciones_numero` (`numero`),
  KEY `fk_devoluciones_sesion_caja_id_sesiones_caja` (`sesion_caja_id`),
  KEY `fk_devoluciones_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_devoluciones_fecha` (`fecha`),
  KEY `ix_devoluciones_sucursal_fecha` (`sucursal_id`,`fecha`),
  KEY `ix_devoluciones_venta_id` (`venta_id`),
  CONSTRAINT `fk_devoluciones_sesion_caja_id_sesiones_caja` FOREIGN KEY (`sesion_caja_id`) REFERENCES `sesiones_caja` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_devoluciones_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_devoluciones_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_devoluciones_venta_id_ventas` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_devoluciones_total_positivo` CHECK ((`total` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `devoluciones`
--

LOCK TABLES `devoluciones` WRITE;
/*!40000 ALTER TABLE `devoluciones` DISABLE KEYS */;
/*!40000 ALTER TABLE `devoluciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `empresa`
--

DROP TABLE IF EXISTS `empresa`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `empresa` (
  `id` int NOT NULL,
  `ruc` varchar(11) NOT NULL,
  `razon_social` varchar(200) NOT NULL,
  `nombre_comercial` varchar(200) DEFAULT NULL,
  `direccion_fiscal` varchar(250) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `logo_url` varchar(300) DEFAULT NULL,
  `igv_porcentaje` decimal(5,2) NOT NULL,
  `icbper_monto` decimal(12,2) NOT NULL DEFAULT '0.50',
  `precios_incluyen_igv` tinyint(1) NOT NULL DEFAULT '1',
  `moneda` varchar(3) NOT NULL DEFAULT 'PEN',
  `simbolo_moneda` varchar(5) NOT NULL DEFAULT 'S/',
  `mensaje_ticket` varchar(300) DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  CONSTRAINT `ck_empresa_fila_unica` CHECK ((`id` = 1)),
  CONSTRAINT `ck_empresa_icbper_no_negativo` CHECK ((`icbper_monto` >= 0)),
  CONSTRAINT `ck_empresa_igv_valido` CHECK (((`igv_porcentaje` >= 0) and (`igv_porcentaje` <= 100)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `empresa`
--

LOCK TABLES `empresa` WRITE;
/*!40000 ALTER TABLE `empresa` DISABLE KEYS */;
INSERT INTO `empresa` VALUES (1,'20000000001','MI MINIMARKET S.A.C.','Mi Minimarket','Av. Principal 123, Lima',NULL,NULL,NULL,18.00,0.50,1,'PEN','S/','¡Gracias por su compra!','2026-10-22 22:00:51','2026-10-22 22:00:51');
/*!40000 ALTER TABLE `empresa` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historial_precios`
--

DROP TABLE IF EXISTS `historial_precios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historial_precios` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `presentacion_id` int DEFAULT NULL,
  `tipo` varchar(30) NOT NULL,
  `precio_anterior` decimal(14,4) NOT NULL,
  `precio_nuevo` decimal(14,4) NOT NULL,
  `origen` varchar(30) NOT NULL,
  `referencia_id` bigint DEFAULT NULL,
  `usuario_id` int DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `fk_historial_precios_presentacion_id_producto_presentaciones` (`presentacion_id`),
  KEY `fk_historial_precios_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_historial_precios_creado_en` (`creado_en`),
  KEY `ix_historial_precios_producto_fecha` (`producto_id`,`creado_en`),
  CONSTRAINT `fk_historial_precios_presentacion_id_producto_presentaciones` FOREIGN KEY (`presentacion_id`) REFERENCES `producto_presentaciones` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_historial_precios_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_historial_precios_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historial_precios`
--

LOCK TABLES `historial_precios` WRITE;
/*!40000 ALTER TABLE `historial_precios` DISABLE KEYS */;
INSERT INTO `historial_precios` VALUES (1,3,NULL,'COSTO',0.0000,3.9500,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(2,4,NULL,'COSTO',0.0000,3.2000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(3,5,NULL,'COSTO',0.0000,9.4000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(4,6,NULL,'COSTO',0.0000,2.8500,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(5,7,NULL,'COSTO',0.0000,5.3000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(6,8,NULL,'COSTO',0.0000,3.3000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(7,9,NULL,'COSTO',0.0000,5.4000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(8,10,NULL,'COSTO',0.0000,2.1000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(9,11,NULL,'COSTO',0.0000,1.1000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(10,12,NULL,'COSTO',0.0000,2.9000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(11,13,NULL,'COSTO',0.0000,3.4000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(12,14,NULL,'COSTO',0.0000,5.8000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(13,15,NULL,'COSTO',0.0000,4.9000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(14,17,NULL,'COSTO',0.0000,5.1000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(15,18,NULL,'COSTO',0.0000,14.5000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(16,19,NULL,'COSTO',0.0000,7.3000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(17,20,NULL,'COSTO',0.0000,0.4500,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(18,21,NULL,'COSTO',0.0000,0.1200,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(19,22,NULL,'COSTO',0.0000,6.9000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(20,23,NULL,'COSTO',0.0000,2.4000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(21,24,NULL,'COSTO',0.0000,1.7000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(22,25,NULL,'COSTO',0.0000,1.0500,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(23,27,NULL,'COSTO',0.0000,7.8000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(24,28,NULL,'COSTO',0.0000,3.1000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(25,29,NULL,'COSTO',0.0000,4.2000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(26,30,NULL,'COSTO',0.0000,5.2000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(27,31,NULL,'COSTO',0.0000,2.9000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(28,32,NULL,'COSTO',0.0000,4.4000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(29,33,NULL,'COSTO',0.0000,2.4000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(30,34,NULL,'COSTO',0.0000,3.0000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(31,35,NULL,'COSTO',0.0000,4.5000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(32,36,NULL,'COSTO',0.0000,6.6000,'STOCK_INICIAL',NULL,1,'2026-10-23 16:20:58'),(33,16,NULL,'COSTO',0.0000,3.4000,'MANUAL',NULL,1,'2026-10-23 16:28:48'),(34,26,NULL,'COSTO',0.0000,0.8000,'MANUAL',NULL,1,'2026-10-23 16:28:48');
/*!40000 ALTER TABLE `historial_precios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `impresoras`
--

DROP TABLE IF EXISTS `impresoras`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `impresoras` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sucursal_id` int NOT NULL,
  `caja_id` int DEFAULT NULL,
  `nombre` varchar(80) NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `conexion` varchar(30) NOT NULL,
  `direccion` varchar(150) DEFAULT NULL,
  `predeterminada` tinyint(1) NOT NULL DEFAULT '0',
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `sucursal_predeterminada_id` int GENERATED ALWAYS AS ((case when `predeterminada` then `sucursal_id` end)) STORED,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_impresoras_sucursal_predeterminada_id` (`sucursal_predeterminada_id`),
  KEY `ix_impresoras_caja_id` (`caja_id`),
  KEY `ix_impresoras_sucursal_id` (`sucursal_id`),
  CONSTRAINT `fk_impresoras_caja_id_cajas` FOREIGN KEY (`caja_id`) REFERENCES `cajas` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_impresoras_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `impresoras`
--

LOCK TABLES `impresoras` WRITE;
/*!40000 ALTER TABLE `impresoras` DISABLE KEYS */;
INSERT INTO `impresoras` (`id`, `sucursal_id`, `caja_id`, `nombre`, `tipo`, `conexion`, `direccion`, `predeterminada`, `activo`, `creado_en`, `actualizado_en`) VALUES (1,1,1,'Ticketera 80mm','TERMICA_80','NAVEGADOR',NULL,1,1,'2026-10-22 22:00:50','2026-10-22 22:00:50');
/*!40000 ALTER TABLE `impresoras` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `inventarios_fisicos`
--

DROP TABLE IF EXISTS `inventarios_fisicos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `inventarios_fisicos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `numero` varchar(20) NOT NULL,
  `almacen_id` int NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'EN_PROCESO',
  `categoria_id` int DEFAULT NULL,
  `usuario_id` int NOT NULL,
  `fecha_aplicacion` datetime DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  `aprobado_por_id` int DEFAULT NULL,
  `motivo_rechazo` varchar(300) DEFAULT NULL,
  `fecha_envio` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_inventarios_fisicos_numero` (`numero`),
  KEY `fk_inventarios_fisicos_categoria_id_categorias` (`categoria_id`),
  KEY `fk_inventarios_fisicos_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_inventarios_fisicos_almacen_id` (`almacen_id`),
  KEY `ix_inventarios_fisicos_estado` (`estado`),
  KEY `fk_inventarios_fisicos_aprobado_por_id_usuarios` (`aprobado_por_id`),
  CONSTRAINT `fk_inventarios_fisicos_almacen_id_almacenes` FOREIGN KEY (`almacen_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_inventarios_fisicos_aprobado_por_id_usuarios` FOREIGN KEY (`aprobado_por_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_inventarios_fisicos_categoria_id_categorias` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_inventarios_fisicos_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `inventarios_fisicos`
--

LOCK TABLES `inventarios_fisicos` WRITE;
/*!40000 ALTER TABLE `inventarios_fisicos` DISABLE KEYS */;
/*!40000 ALTER TABLE `inventarios_fisicos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `lotes`
--

DROP TABLE IF EXISTS `lotes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `lotes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `almacen_id` int NOT NULL,
  `numero_lote` varchar(50) NOT NULL,
  `fecha_vencimiento` date DEFAULT NULL,
  `cantidad_inicial` decimal(12,3) NOT NULL,
  `cantidad_actual` decimal(12,3) NOT NULL,
  `costo_unitario` decimal(14,4) NOT NULL DEFAULT '0.0000',
  `compra_id` int DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_lotes_producto_id_almacen_id_numero_lote` (`producto_id`,`almacen_id`,`numero_lote`),
  KEY `fk_lotes_compra_id_compras` (`compra_id`),
  KEY `ix_lotes_almacen_producto_vencimiento` (`almacen_id`,`producto_id`,`fecha_vencimiento`),
  KEY `ix_lotes_fecha_vencimiento` (`fecha_vencimiento`),
  KEY `ix_lotes_producto_id` (`producto_id`),
  CONSTRAINT `fk_lotes_almacen_id_almacenes` FOREIGN KEY (`almacen_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_lotes_compra_id_compras` FOREIGN KEY (`compra_id`) REFERENCES `compras` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_lotes_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_lotes_cantidad_actual_no_negativa` CHECK ((`cantidad_actual` >= 0)),
  CONSTRAINT `ck_lotes_cantidad_inicial_no_negativa` CHECK ((`cantidad_inicial` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `lotes`
--

LOCK TABLES `lotes` WRITE;
/*!40000 ALTER TABLE `lotes` DISABLE KEYS */;
INSERT INTO `lotes` VALUES (1,8,1,'LG-1022','2027-02-20',72.000,72.000,3.3000,NULL,1,'2026-10-23 16:20:58','2026-10-23 16:20:58'),(2,8,1,'LG-1030','2027-03-22',24.000,24.000,3.3000,NULL,1,'2026-10-23 16:20:58','2026-10-23 16:20:58'),(3,17,1,'L-0921','2026-10-25',6.000,6.000,5.1000,NULL,1,'2026-10-23 16:20:58','2026-10-23 16:20:58'),(4,17,1,'L-0950','2026-11-10',6.000,6.000,5.1000,NULL,1,'2026-10-23 16:20:58','2026-10-23 16:20:58'),(5,18,1,'Q-118','2026-11-04',4.000,4.000,14.5000,NULL,1,'2026-10-23 16:20:58','2026-10-23 16:20:58'),(6,22,1,'PM-77','2026-11-17',8.000,8.000,6.9000,NULL,1,'2026-10-23 16:20:58','2026-10-23 16:20:58'),(7,36,1,'HD-3310','2026-10-27',5.000,5.000,6.6000,NULL,1,'2026-10-23 16:20:58','2026-10-23 16:20:58');
/*!40000 ALTER TABLE `lotes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `marcas`
--

DROP TABLE IF EXISTS `marcas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `marcas` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_marcas_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `marcas`
--

LOCK TABLES `marcas` WRITE;
/*!40000 ALTER TABLE `marcas` DISABLE KEYS */;
INSERT INTO `marcas` VALUES (1,'Costeño',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(2,'Dulfina',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(3,'Primor',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(4,'Don Vittorio',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(5,'Florida',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(6,'Gloria',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(7,'Inca Kola',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(8,'Coca-Cola',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(9,'San Luis',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(10,'Backus',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(11,'Frugos',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(12,'Red Bull',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(13,'Pilsen',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(14,'Cusqueña',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(15,'Laive',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(16,'Bimbo',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(17,'Field',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(18,'Lay\'s',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(19,'Nestlé',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(20,'Oreo',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(21,'Bolívar',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(22,'Clorox',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(23,'Ayudín',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(24,'Elite',1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(25,'Protex',1,'2026-10-23 16:20:58','2026-10-23 16:20:58'),(26,'Colgate',1,'2026-10-23 16:20:58','2026-10-23 16:20:58'),(27,'San Fernando',1,'2026-10-23 16:20:58','2026-10-23 16:20:58');
/*!40000 ALTER TABLE `marcas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `motivos_ajuste`
--

DROP TABLE IF EXISTS `motivos_ajuste`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `motivos_ajuste` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(80) NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `es_merma` tinyint(1) NOT NULL DEFAULT '0',
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_motivos_ajuste_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `motivos_ajuste`
--

LOCK TABLES `motivos_ajuste` WRITE;
/*!40000 ALTER TABLE `motivos_ajuste` DISABLE KEYS */;
INSERT INTO `motivos_ajuste` VALUES (1,'Producto vencido','SALIDA',1,1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(2,'Producto dañado o roto','SALIDA',1,1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(3,'Robo o pérdida','SALIDA',1,1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(4,'Consumo interno','SALIDA',0,1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(5,'Sobrante encontrado','ENTRADA',0,1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(6,'Bonificación del proveedor','ENTRADA',0,1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),(7,'Corrección de error de registro','AMBOS',0,1,'2026-10-22 22:00:51','2026-10-22 22:00:51');
/*!40000 ALTER TABLE `motivos_ajuste` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimientos_caja`
--

DROP TABLE IF EXISTS `movimientos_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimientos_caja` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sesion_caja_id` int NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `concepto` varchar(200) NOT NULL,
  `usuario_id` int NOT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `fk_movimientos_caja_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_movimientos_caja_creado_en` (`creado_en`),
  KEY `ix_movimientos_caja_sesion_caja_id` (`sesion_caja_id`),
  CONSTRAINT `fk_movimientos_caja_sesion_caja_id_sesiones_caja` FOREIGN KEY (`sesion_caja_id`) REFERENCES `sesiones_caja` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_movimientos_caja_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_movimientos_caja_monto_positivo` CHECK ((`monto` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimientos_caja`
--

LOCK TABLES `movimientos_caja` WRITE;
/*!40000 ALTER TABLE `movimientos_caja` DISABLE KEYS */;
/*!40000 ALTER TABLE `movimientos_caja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `movimientos_inventario`
--

DROP TABLE IF EXISTS `movimientos_inventario`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `movimientos_inventario` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `almacen_id` int NOT NULL,
  `lote_id` int DEFAULT NULL,
  `tipo` varchar(30) NOT NULL,
  `cantidad` decimal(12,3) NOT NULL,
  `stock_anterior` decimal(12,3) NOT NULL,
  `stock_nuevo` decimal(12,3) NOT NULL,
  `costo_unitario` decimal(14,4) NOT NULL DEFAULT '0.0000',
  `referencia_tipo` varchar(30) DEFAULT NULL,
  `referencia_id` bigint DEFAULT NULL,
  `motivo` varchar(300) DEFAULT NULL,
  `usuario_id` int DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `fk_movimientos_inventario_lote_id_lotes` (`lote_id`),
  KEY `fk_movimientos_inventario_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_movimientos_inventario_almacen_fecha` (`almacen_id`,`creado_en`),
  KEY `ix_movimientos_inventario_creado_en` (`creado_en`),
  KEY `ix_movimientos_inventario_producto_almacen_fecha` (`producto_id`,`almacen_id`,`creado_en`),
  KEY `ix_movimientos_inventario_referencia` (`referencia_tipo`,`referencia_id`),
  KEY `ix_movimientos_inventario_tipo` (`tipo`),
  CONSTRAINT `fk_movimientos_inventario_almacen_id_almacenes` FOREIGN KEY (`almacen_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_movimientos_inventario_lote_id_lotes` FOREIGN KEY (`lote_id`) REFERENCES `lotes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_movimientos_inventario_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_movimientos_inventario_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=45 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `movimientos_inventario`
--

LOCK TABLES `movimientos_inventario` WRITE;
/*!40000 ALTER TABLE `movimientos_inventario` DISABLE KEYS */;
INSERT INTO `movimientos_inventario` VALUES (1,3,1,NULL,'STOCK_INICIAL',33.000,0.000,33.000,3.9500,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(2,4,1,NULL,'STOCK_INICIAL',5.000,0.000,5.000,3.2000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(3,5,1,NULL,'STOCK_INICIAL',3.000,0.000,3.000,9.4000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(4,6,1,NULL,'STOCK_INICIAL',40.000,0.000,40.000,2.8500,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(5,7,1,NULL,'STOCK_INICIAL',36.000,0.000,36.000,5.3000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(6,8,1,1,'STOCK_INICIAL',72.000,0.000,72.000,3.3000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(7,8,1,2,'STOCK_INICIAL',24.000,72.000,96.000,3.3000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(8,9,1,NULL,'STOCK_INICIAL',48.000,0.000,48.000,5.4000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(9,10,1,NULL,'STOCK_INICIAL',36.000,0.000,36.000,2.1000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(10,11,1,NULL,'STOCK_INICIAL',60.000,0.000,60.000,1.1000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(11,12,1,NULL,'STOCK_INICIAL',24.000,0.000,24.000,2.9000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(12,13,1,NULL,'STOCK_INICIAL',18.000,0.000,18.000,3.4000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(13,14,1,NULL,'STOCK_INICIAL',12.000,0.000,12.000,5.8000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(14,15,1,NULL,'STOCK_INICIAL',120.000,0.000,120.000,4.9000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(15,17,1,3,'STOCK_INICIAL',6.000,0.000,6.000,5.1000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(16,17,1,4,'STOCK_INICIAL',6.000,6.000,12.000,5.1000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(17,18,1,5,'STOCK_INICIAL',4.000,0.000,4.000,14.5000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(18,19,1,NULL,'STOCK_INICIAL',10.000,0.000,10.000,7.3000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(19,20,1,NULL,'STOCK_INICIAL',90.000,0.000,90.000,0.4500,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(20,21,1,NULL,'STOCK_INICIAL',180.000,0.000,180.000,0.1200,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(21,22,1,6,'STOCK_INICIAL',8.000,0.000,8.000,6.9000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(22,23,1,NULL,'STOCK_INICIAL',22.000,0.000,22.000,2.4000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(23,24,1,NULL,'STOCK_INICIAL',30.000,0.000,30.000,1.7000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(24,25,1,NULL,'STOCK_INICIAL',50.000,0.000,50.000,1.0500,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(25,27,1,NULL,'STOCK_INICIAL',14.000,0.000,14.000,7.8000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(26,28,1,NULL,'STOCK_INICIAL',20.000,0.000,20.000,3.1000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(27,29,1,NULL,'STOCK_INICIAL',9.000,0.000,9.000,4.2000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(28,30,1,NULL,'STOCK_INICIAL',25.000,0.000,25.000,5.2000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(29,31,1,NULL,'STOCK_INICIAL',18.000,0.000,18.000,2.9000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(30,32,1,NULL,'STOCK_INICIAL',15.000,0.000,15.000,4.4000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(31,33,1,NULL,'STOCK_INICIAL',25.500,0.000,25.500,2.4000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(32,34,1,NULL,'STOCK_INICIAL',40.250,0.000,40.250,3.0000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(33,35,1,NULL,'STOCK_INICIAL',8.750,0.000,8.750,4.5000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(34,36,1,7,'STOCK_INICIAL',5.000,0.000,5.000,6.6000,'stock_inicial',NULL,'Carga de stock inicial',1,'2026-10-23 16:20:58'),(35,3,1,NULL,'SALIDA_VENTA',-1.000,33.000,32.000,3.9500,'venta',3,'Venta T001-00000001',1,'2026-10-23 22:28:16'),(36,11,1,NULL,'SALIDA_VENTA',-2.000,60.000,58.000,1.1000,'venta',3,'Venta T001-00000001',1,'2026-10-23 22:28:16'),(37,7,1,NULL,'SALIDA_VENTA',-3.000,36.000,33.000,5.3000,'venta',4,'Venta T001-00000002',1,'2026-10-23 22:28:16'),(38,15,1,NULL,'SALIDA_VENTA',-1.000,120.000,119.000,4.9000,'venta',5,'Venta T001-00000003',1,'2026-10-23 22:28:16'),(39,25,1,NULL,'SALIDA_VENTA',-2.000,50.000,48.000,1.0500,'venta',5,'Venta T001-00000003',1,'2026-10-23 22:28:16'),(40,3,1,NULL,'SALIDA_VENTA',-1.000,32.000,31.000,3.9500,'venta',6,'Venta T001-00000004',1,'2026-10-23 22:42:09'),(41,11,1,NULL,'SALIDA_VENTA',-2.000,58.000,56.000,1.1000,'venta',6,'Venta T001-00000004',1,'2026-10-23 22:42:09'),(42,25,1,NULL,'SALIDA_VENTA',-1.000,48.000,47.000,1.0500,'venta',6,'Venta T001-00000004',1,'2026-10-23 22:42:09'),(43,27,1,NULL,'SALIDA_VENTA',-2.000,14.000,12.000,7.8000,'venta',6,'Venta T001-00000004',1,'2026-10-23 22:42:09'),(44,33,1,NULL,'SALIDA_VENTA',-1.250,25.500,24.250,2.4000,'venta',6,'Venta T001-00000004',1,'2026-10-23 22:42:09');
/*!40000 ALTER TABLE `movimientos_inventario` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`minimarket`@`localhost`*/ /*!50003 TRIGGER `trg_kardex_sin_modificar` BEFORE UPDATE ON `movimientos_inventario` FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El kardex no se puede modificar' */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_0900_ai_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`minimarket`@`localhost`*/ /*!50003 TRIGGER `trg_kardex_sin_borrar` BEFORE DELETE ON `movimientos_inventario` FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'El kardex no se puede borrar' */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `operaciones_idempotentes`
--

DROP TABLE IF EXISTS `operaciones_idempotentes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operaciones_idempotentes` (
  `usuario_id` int NOT NULL,
  `clave` varchar(64) NOT NULL,
  `operacion` varchar(40) NOT NULL,
  `referencia_id` bigint DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`usuario_id`,`clave`),
  KEY `ix_operaciones_idempotentes_creado_en` (`creado_en`),
  CONSTRAINT `fk_operaciones_idempotentes_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operaciones_idempotentes`
--

LOCK TABLES `operaciones_idempotentes` WRITE;
/*!40000 ALTER TABLE `operaciones_idempotentes` DISABLE KEYS */;
INSERT INTO `operaciones_idempotentes` VALUES (1,'5ce06e17f3ee4265bd9e72eba0eb577d','venta',5,'2026-10-23 22:28:16'),(1,'824bee8123824c988ddde55c87530b6c','venta',4,'2026-10-23 22:28:16'),(1,'a1aaa28fe25f43308d26ed7389c64b56','venta',3,'2026-10-23 22:28:16'),(1,'c1cc088e16654d1e86cc6cdf6475fbcb','abrir_caja',5,'2026-10-23 22:28:16'),(1,'captura1792795324304','venta',6,'2026-10-23 22:42:09');
/*!40000 ALTER TABLE `operaciones_idempotentes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pagos_proveedor`
--

DROP TABLE IF EXISTS `pagos_proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pagos_proveedor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `cuenta_por_pagar_id` int NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `metodo` varchar(30) NOT NULL,
  `referencia` varchar(100) DEFAULT NULL,
  `sesion_caja_id` int DEFAULT NULL,
  `usuario_id` int NOT NULL,
  `fecha` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `fk_pagos_proveedor_sesion_caja_id_sesiones_caja` (`sesion_caja_id`),
  KEY `fk_pagos_proveedor_usuario_id_usuarios` (`usuario_id`),
  KEY `ix_pagos_proveedor_cuenta_por_pagar_id` (`cuenta_por_pagar_id`),
  KEY `ix_pagos_proveedor_fecha` (`fecha`),
  CONSTRAINT `fk_pagos_proveedor_cuenta_por_pagar_id_cuentas_por_pagar` FOREIGN KEY (`cuenta_por_pagar_id`) REFERENCES `cuentas_por_pagar` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pagos_proveedor_sesion_caja_id_sesiones_caja` FOREIGN KEY (`sesion_caja_id`) REFERENCES `sesiones_caja` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_pagos_proveedor_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_pagos_proveedor_monto_positivo` CHECK ((`monto` > 0))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pagos_proveedor`
--

LOCK TABLES `pagos_proveedor` WRITE;
/*!40000 ALTER TABLE `pagos_proveedor` DISABLE KEYS */;
/*!40000 ALTER TABLE `pagos_proveedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `pagos_venta`
--

DROP TABLE IF EXISTS `pagos_venta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pagos_venta` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `venta_id` bigint NOT NULL,
  `metodo` varchar(30) NOT NULL,
  `monto` decimal(12,2) NOT NULL,
  `monto_recibido` decimal(12,2) DEFAULT NULL,
  `referencia` varchar(100) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_pagos_venta_metodo` (`metodo`),
  KEY `ix_pagos_venta_venta_id` (`venta_id`),
  CONSTRAINT `fk_pagos_venta_venta_id_ventas` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_pagos_venta_monto_positivo` CHECK ((`monto` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `pagos_venta`
--

LOCK TABLES `pagos_venta` WRITE;
/*!40000 ALTER TABLE `pagos_venta` DISABLE KEYS */;
INSERT INTO `pagos_venta` VALUES (1,3,'EFECTIVO',8.10,50.00,NULL),(2,4,'YAPE',20.70,NULL,'123456'),(3,5,'TARJETA',9.50,NULL,NULL),(4,6,'EFECTIVO',33.78,50.00,NULL);
/*!40000 ALTER TABLE `pagos_venta` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `parametros_sistema`
--

DROP TABLE IF EXISTS `parametros_sistema`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parametros_sistema` (
  `clave` varchar(80) NOT NULL,
  `valor` json NOT NULL,
  `tipo` varchar(30) NOT NULL,
  `modulo` varchar(40) NOT NULL,
  `descripcion` varchar(250) NOT NULL,
  `editable` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`clave`),
  KEY `ix_parametros_sistema_modulo` (`modulo`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `parametros_sistema`
--

LOCK TABLES `parametros_sistema` WRITE;
/*!40000 ALTER TABLE `parametros_sistema` DISABLE KEYS */;
INSERT INTO `parametros_sistema` VALUES ('caja.denominaciones','[\"200\", \"100\", \"50\", \"20\", \"10\", \"5\", \"2\", \"1\", \"0.50\", \"0.20\", \"0.10\"]','JSON','caja','Billetes y monedas usados en el arqueo',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),('clientes.dias_credito_defecto','30','ENTERO','clientes','Días de plazo por defecto para ventas al fiado',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),('inventario.dias_alerta_vencimiento','30','ENTERO','inventario','Días de anticipación para alertar productos por vencer',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),('seguridad.max_intentos_ip','20','ENTERO','seguridad','Ingresos fallidos permitidos desde un mismo equipo (IP) dentro de la ventana',1,'2026-10-23 15:16:03','2026-10-23 15:16:03'),('seguridad.max_intentos_login','5','ENTERO','seguridad','Intentos fallidos antes de bloquear el usuario',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),('seguridad.minutos_bloqueo','15','ENTERO','seguridad','Minutos de bloqueo tras superar los intentos',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),('seguridad.minutos_ventana_ip','15','ENTERO','seguridad','Minutos que se cuentan los ingresos fallidos de un mismo equipo (IP)',1,'2026-10-23 15:16:03','2026-10-23 15:16:03'),('ventas.cliente_obligatorio_desde','\"700.00\"','DECIMAL','ventas','Monto desde el cual la boleta exige identificar al cliente (DNI)',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),('ventas.descuento_maximo_cajero','\"10\"','DECIMAL','ventas','Descuento máximo (%) que puede aplicar un cajero sin autorización',1,'2026-10-22 22:00:51','2026-10-22 22:00:51'),('ventas.redondeo_efectivo','\"0.00\"','DECIMAL','ventas','Redondeo del total en efectivo (0.00 = sin redondeo, 0.10 = a 10 céntimos)',1,'2026-10-22 22:00:51','2026-10-22 22:00:51');
/*!40000 ALTER TABLE `parametros_sistema` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `permisos`
--

DROP TABLE IF EXISTS `permisos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `permisos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(80) NOT NULL,
  `modulo` varchar(40) NOT NULL,
  `accion` varchar(40) NOT NULL,
  `descripcion` varchar(200) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_permisos_codigo` (`codigo`),
  KEY `ix_permisos_modulo` (`modulo`)
) ENGINE=InnoDB AUTO_INCREMENT=65 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permisos`
--

LOCK TABLES `permisos` WRITE;
/*!40000 ALTER TABLE `permisos` DISABLE KEYS */;
INSERT INTO `permisos` VALUES (1,'dashboard.ver','dashboard','ver','Ver el dashboard'),(2,'pos.vender','pos','vender','Registrar ventas en el punto de venta'),(3,'pos.aplicar_descuento','pos','aplicar_descuento','Aplicar descuentos en ventas'),(4,'pos.venta_credito','pos','venta_credito','Registrar ventas al fiado'),(5,'pos.devolver','pos','devolver','Registrar devoluciones de productos'),(6,'pos.anular_venta','pos','anular_venta','Anular ventas'),(7,'caja.ver','caja','ver','Ver su caja'),(8,'caja.abrir','caja','abrir','Abrir caja'),(9,'caja.cerrar','caja','cerrar','Cerrar caja y hacer arqueo'),(10,'caja.movimientos','caja','movimientos','Registrar ingresos y egresos de caja'),(11,'caja.ver_todas','caja','ver_todas','Ver cajas e historial de todos los cajeros'),(12,'productos.ver','productos','ver','Ver productos'),(13,'productos.crear','productos','crear','Crear productos'),(14,'productos.editar','productos','editar','Editar productos y precios'),(15,'productos.eliminar','productos','eliminar','Eliminar productos'),(16,'productos.importar','productos','importar','Importar productos desde Excel'),(17,'productos.exportar','productos','exportar','Exportar productos a Excel'),(18,'categorias.ver','categorias','ver','Ver categorías'),(19,'categorias.crear','categorias','crear','Crear categorías'),(20,'categorias.editar','categorias','editar','Editar categorías'),(21,'categorias.eliminar','categorias','eliminar','Eliminar categorías'),(22,'marcas.ver','marcas','ver','Ver marcas'),(23,'marcas.crear','marcas','crear','Crear marcas'),(24,'marcas.editar','marcas','editar','Editar marcas'),(25,'marcas.eliminar','marcas','eliminar','Eliminar marcas'),(26,'inventario.ver','inventario','ver','Ver stock y lotes'),(27,'inventario.kardex','inventario','kardex','Ver kardex de productos'),(28,'inventario.ajustar','inventario','ajustar','Registrar ajustes y mermas'),(29,'inventario.aprobar_ajustes','inventario','aprobar_ajustes','Aprobar ajustes, mermas e inventarios físicos'),(30,'inventario.inventario_fisico','inventario','inventario_fisico','Realizar inventario físico'),(31,'inventario.transferir','inventario','transferir','Enviar transferencias entre almacenes'),(32,'inventario.recibir_transferencia','inventario','recibir_transferencia','Recibir transferencias entre almacenes'),(33,'sucursales.ver','sucursales','ver','Ver sucursales y almacenes'),(34,'sucursales.gestionar','sucursales','gestionar','Crear y modificar sucursales, almacenes y cajas'),(35,'sucursales.todas','sucursales','todas','Ver información de todas las sucursales (no solo la actual)'),(36,'proveedores.ver','proveedores','ver','Ver proveedores'),(37,'proveedores.crear','proveedores','crear','Crear proveedores'),(38,'proveedores.editar','proveedores','editar','Editar proveedores'),(39,'proveedores.eliminar','proveedores','eliminar','Eliminar proveedores'),(40,'compras.ver','compras','ver','Ver compras y órdenes de compra'),(41,'compras.crear','compras','crear','Crear órdenes de compra'),(42,'compras.recibir','compras','recibir','Recepcionar mercadería'),(43,'compras.anular','compras','anular','Anular compras'),(44,'compras.pagar','compras','pagar','Registrar pagos a proveedores'),(45,'clientes.ver','clientes','ver','Ver clientes'),(46,'clientes.crear','clientes','crear','Crear clientes'),(47,'clientes.editar','clientes','editar','Editar clientes'),(48,'clientes.eliminar','clientes','eliminar','Eliminar clientes'),(49,'clientes.cobrar','clientes','cobrar','Registrar abonos de cuentas por cobrar'),(50,'reportes.ver','reportes','ver','Ver reportes'),(51,'reportes.ganancias','reportes','ganancias','Ver ganancias y costos'),(52,'reportes.exportar','reportes','exportar','Exportar reportes a PDF y Excel'),(53,'usuarios.ver','usuarios','ver','Ver usuarios'),(54,'usuarios.crear','usuarios','crear','Crear usuarios'),(55,'usuarios.editar','usuarios','editar','Editar usuarios'),(56,'usuarios.eliminar','usuarios','eliminar','Desactivar usuarios'),(57,'roles.ver','roles','ver','Ver roles y permisos'),(58,'roles.gestionar','roles','gestionar','Crear y modificar roles y permisos'),(59,'configuracion.ver','configuracion','ver','Ver configuración'),(60,'configuracion.editar','configuracion','editar','Modificar configuración de la empresa'),(61,'auditoria.ver','auditoria','ver','Ver auditoría de acciones'),(62,'pos.vender_sin_stock','pos','vender_sin_stock','Vender productos sin stock suficiente (el stock queda negativo por regularizar)'),(63,'inventario.stock_inicial','inventario','stock_inicial','Cargar el stock inicial de productos'),(64,'inventario.integridad','inventario','integridad','Revisar la integridad del stock (stock = kardex = lotes)');
/*!40000 ALTER TABLE `permisos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producto_presentaciones`
--

DROP TABLE IF EXISTS `producto_presentaciones`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto_presentaciones` (
  `id` int NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `nombre` varchar(80) NOT NULL,
  `factor` decimal(12,3) NOT NULL,
  `precio_venta` decimal(12,2) NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_producto_presentaciones_producto_id_nombre` (`producto_id`,`nombre`),
  KEY `ix_producto_presentaciones_producto_id` (`producto_id`),
  CONSTRAINT `fk_producto_presentaciones_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_producto_presentaciones_factor_positivo` CHECK ((`factor` > 0)),
  CONSTRAINT `ck_producto_presentaciones_precio_venta_no_negativo` CHECK ((`precio_venta` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto_presentaciones`
--

LOCK TABLES `producto_presentaciones` WRITE;
/*!40000 ALTER TABLE `producto_presentaciones` DISABLE KEYS */;
INSERT INTO `producto_presentaciones` VALUES (3,10,'Six pack',6.000,16.50,1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(4,15,'Caja x12',12.000,72.00,1,'2026-10-23 16:20:57','2026-10-23 16:20:57'),(5,25,'Caja x24',24.000,33.00,1,'2026-10-23 16:20:57','2026-10-23 16:20:57');
/*!40000 ALTER TABLE `producto_presentaciones` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `producto_proveedor`
--

DROP TABLE IF EXISTS `producto_proveedor`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `producto_proveedor` (
  `id` int NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `proveedor_id` int NOT NULL,
  `codigo_proveedor` varchar(50) DEFAULT NULL,
  `ultimo_costo` decimal(14,4) DEFAULT NULL,
  `fecha_ultima_compra` date DEFAULT NULL,
  `es_principal` tinyint(1) NOT NULL DEFAULT '0',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_producto_proveedor_producto_id_proveedor_id` (`producto_id`,`proveedor_id`),
  KEY `ix_producto_proveedor_producto_id` (`producto_id`),
  KEY `ix_producto_proveedor_proveedor_id` (`proveedor_id`),
  CONSTRAINT `fk_producto_proveedor_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_producto_proveedor_proveedor_id_proveedores` FOREIGN KEY (`proveedor_id`) REFERENCES `proveedores` (`id`) ON DELETE CASCADE,
  CONSTRAINT `ck_producto_proveedor_ultimo_costo_no_negativo` CHECK (((`ultimo_costo` is null) or (`ultimo_costo` >= 0)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `producto_proveedor`
--

LOCK TABLES `producto_proveedor` WRITE;
/*!40000 ALTER TABLE `producto_proveedor` DISABLE KEYS */;
/*!40000 ALTER TABLE `producto_proveedor` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `productos`
--

DROP TABLE IF EXISTS `productos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `productos` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo_interno` varchar(30) DEFAULT NULL,
  `nombre` varchar(200) NOT NULL,
  `descripcion` text,
  `categoria_id` int DEFAULT NULL,
  `marca_id` int DEFAULT NULL,
  `unidad_medida` varchar(30) NOT NULL DEFAULT 'UNIDAD',
  `precio_costo` decimal(14,4) NOT NULL DEFAULT '0.0000',
  `precio_venta` decimal(12,2) NOT NULL DEFAULT '0.00',
  `stock_minimo` decimal(12,3) NOT NULL DEFAULT '0.000',
  `tipo_afectacion_igv` varchar(30) NOT NULL DEFAULT 'GRAVADO',
  `afecto_icbper` tinyint(1) NOT NULL DEFAULT '0',
  `maneja_lotes` tinyint(1) NOT NULL DEFAULT '0',
  `permite_decimales` tinyint(1) NOT NULL DEFAULT '0',
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  `imagen` varchar(60) DEFAULT NULL,
  `version` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_productos_codigo_interno` (`codigo_interno`),
  KEY `ix_productos_categoria_activo` (`categoria_id`,`activo`),
  KEY `ix_productos_marca_id` (`marca_id`),
  KEY `ix_productos_nombre` (`nombre`),
  FULLTEXT KEY `ftx_productos_nombre` (`nombre`) /*!50100 WITH PARSER `ngram` */ ,
  CONSTRAINT `fk_productos_categoria_id_categorias` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_productos_marca_id_marcas` FOREIGN KEY (`marca_id`) REFERENCES `marcas` (`id`) ON DELETE SET NULL,
  CONSTRAINT `ck_productos_precio_costo_no_negativo` CHECK ((`precio_costo` >= 0)),
  CONSTRAINT `ck_productos_precio_venta_no_negativo` CHECK ((`precio_venta` >= 0)),
  CONSTRAINT `ck_productos_stock_minimo_no_negativo` CHECK ((`stock_minimo` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=37 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `productos`
--

LOCK TABLES `productos` WRITE;
/*!40000 ALTER TABLE `productos` DISABLE KEYS */;
INSERT INTO `productos` VALUES (3,NULL,'Arroz Costeño extra 1 kg',NULL,1,1,'UNIDAD',3.9500,4.50,20.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(4,NULL,'Azúcar rubia Dulfina 1 kg',NULL,1,2,'UNIDAD',3.2000,3.80,20.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(5,NULL,'Aceite Primor premium 1 L',NULL,1,3,'UNIDAD',9.4000,11.50,12.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(6,NULL,'Fideo spaghetti Don Vittorio 500 g',NULL,1,4,'UNIDAD',2.8500,3.60,15.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(7,NULL,'Atún Florida filete 170 g',NULL,1,5,'UNIDAD',5.3000,6.90,12.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(8,NULL,'Leche Gloria evaporada 400 g',NULL,3,6,'UNIDAD',3.3000,4.20,48.000,'GRAVADO',0,1,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(9,NULL,'Gaseosa Inca Kola 1.5 L',NULL,2,7,'UNIDAD',5.4000,7.50,24.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(10,NULL,'Gaseosa Coca-Cola 500 ml',NULL,2,8,'UNIDAD',2.1000,3.00,24.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(11,NULL,'Agua San Luis sin gas 625 ml',NULL,2,9,'UNIDAD',1.1000,1.80,24.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(12,NULL,'Gaseosa Guaraná 1 L',NULL,2,10,'UNIDAD',2.9000,4.00,12.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(13,NULL,'Frugos del Valle durazno 1 L',NULL,2,11,'UNIDAD',3.4000,4.50,12.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(14,NULL,'Red Bull 250 ml',NULL,2,12,'UNIDAD',5.8000,7.50,6.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(15,NULL,'Cerveza Pilsen Callao 630 ml',NULL,8,13,'UNIDAD',4.9000,6.50,48.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(16,NULL,'Cerveza Cusqueña dorada lata 355 ml',NULL,8,14,'UNIDAD',3.4000,4.50,24.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:28:48',NULL,2),(17,NULL,'Yogurt Gloria fresa 1 L',NULL,3,6,'UNIDAD',5.1000,6.90,6.000,'GRAVADO',0,1,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(18,NULL,'Queso fresco Laive 500 g',NULL,3,15,'UNIDAD',14.5000,17.90,3.000,'GRAVADO',0,1,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(19,NULL,'Mantequilla Laive con sal 200 g',NULL,3,15,'UNIDAD',7.3000,9.20,5.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(20,NULL,'Huevos rosados (unidad)',NULL,3,NULL,'UNIDAD',0.4500,0.60,60.000,'EXONERADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(21,NULL,'Pan francés',NULL,4,NULL,'UNIDAD',0.1200,0.20,50.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(22,NULL,'Pan de molde Bimbo blanco',NULL,4,16,'UNIDAD',6.9000,8.90,4.000,'GRAVADO',0,1,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(23,NULL,'Galletas Soda Field paquete x6',NULL,5,17,'UNIDAD',2.4000,3.20,10.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(24,NULL,'Papas Lay\'s clásicas 42 g',NULL,5,18,'UNIDAD',1.7000,2.50,12.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(25,NULL,'Chocolate Sublime clásico 30 g',NULL,5,19,'UNIDAD',1.0500,1.50,24.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(26,NULL,'Galletas Oreo 36 g',NULL,5,20,'UNIDAD',0.8000,1.20,24.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:28:48',NULL,2),(27,NULL,'Detergente Bolívar 750 g',NULL,6,21,'UNIDAD',7.8000,9.90,6.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(28,NULL,'Lejía Clorox 1 L',NULL,6,22,'UNIDAD',3.1000,4.20,8.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(29,NULL,'Lavavajilla Ayudín limón 450 g',NULL,6,23,'UNIDAD',4.2000,5.50,10.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(30,NULL,'Papel higiénico Elite x4',NULL,7,24,'UNIDAD',5.2000,6.90,10.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:57','2026-10-23 16:20:58',NULL,1),(31,NULL,'Jabón Protex avena 110 g',NULL,7,25,'UNIDAD',2.9000,3.90,8.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:58','2026-10-23 16:20:58',NULL,1),(32,NULL,'Pasta dental Colgate triple acción 75 ml',NULL,7,26,'UNIDAD',4.4000,5.90,6.000,'GRAVADO',0,0,0,1,'2026-10-23 16:20:58','2026-10-23 16:20:58',NULL,1),(33,NULL,'Plátano de seda',NULL,10,NULL,'KILOGRAMO',2.4000,3.50,10.000,'EXONERADO',0,0,1,1,'2026-10-23 16:20:58','2026-10-23 16:20:58',NULL,1),(34,NULL,'Papa amarilla',NULL,10,NULL,'KILOGRAMO',3.0000,4.20,15.000,'EXONERADO',0,0,1,1,'2026-10-23 16:20:58','2026-10-23 16:20:58',NULL,1),(35,NULL,'Limón',NULL,10,NULL,'KILOGRAMO',4.5000,6.00,5.000,'EXONERADO',0,0,1,1,'2026-10-23 16:20:58','2026-10-23 16:20:58',NULL,1),(36,NULL,'Hot dog San Fernando x10',NULL,9,27,'UNIDAD',6.6000,8.50,4.000,'GRAVADO',0,1,0,1,'2026-10-23 16:20:58','2026-10-23 16:20:58',NULL,1);
/*!40000 ALTER TABLE `productos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `proveedores`
--

DROP TABLE IF EXISTS `proveedores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `proveedores` (
  `id` int NOT NULL AUTO_INCREMENT,
  `ruc` varchar(11) NOT NULL,
  `razon_social` varchar(200) NOT NULL,
  `nombre_comercial` varchar(200) DEFAULT NULL,
  `direccion` varchar(250) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `email` varchar(150) DEFAULT NULL,
  `contacto` varchar(150) DEFAULT NULL,
  `dias_credito` int NOT NULL DEFAULT '0',
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_proveedores_ruc` (`ruc`),
  FULLTEXT KEY `ftx_proveedores_razon_social` (`razon_social`) /*!50100 WITH PARSER `ngram` */ 
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `proveedores`
--

LOCK TABLES `proveedores` WRITE;
/*!40000 ALTER TABLE `proveedores` DISABLE KEYS */;
/*!40000 ALTER TABLE `proveedores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `refresh_tokens`
--

DROP TABLE IF EXISTS `refresh_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `refresh_tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `usuario_id` int NOT NULL,
  `jti_hash` varchar(64) NOT NULL,
  `expira_en` datetime NOT NULL,
  `revocado` tinyint(1) NOT NULL DEFAULT '0',
  `ip` varchar(45) DEFAULT NULL,
  `user_agent` varchar(300) DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `sucursal_id` int NOT NULL,
  `revocado_en` datetime DEFAULT NULL,
  `motivo_revocacion` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_refresh_tokens_jti_hash` (`jti_hash`),
  KEY `ix_refresh_tokens_expira_en` (`expira_en`),
  KEY `ix_refresh_tokens_usuario_id` (`usuario_id`),
  KEY `fk_refresh_tokens_sucursal_id_sucursales` (`sucursal_id`),
  CONSTRAINT `fk_refresh_tokens_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_refresh_tokens_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=240 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `refresh_tokens`
--

LOCK TABLES `refresh_tokens` WRITE;
/*!40000 ALTER TABLE `refresh_tokens` DISABLE KEYS */;
INSERT INTO `refresh_tokens` VALUES (109,1,'1643d0dadb5c5c198abbcde2f4edae251ae0f2c3e476cf728327fd842b43af6e','2026-10-29 23:11:26',0,'127.0.0.1','python-httpx/0.28.1','2026-10-22 23:11:26',1,NULL,NULL),(110,1,'bbef58daa12aa6388601418719b3e031462be8ee61f9588918640c0140506b7a','2026-10-30 14:14:20',1,'127.0.0.1','node','2026-10-23 14:14:20',1,'2026-10-23 14:14:20','ROTACION'),(111,1,'2c3b8e75f7b2bf2d5377c3e3df092d31c3970cd2860b8ac5b66b82b2a6565477','2026-10-30 14:14:20',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:14:20',1,NULL,NULL),(112,1,'85f3a300f9c48b830352595f8c678fb36f3474965f33733b965503dee27d4f11','2026-10-30 14:14:23',1,'127.0.0.1','node','2026-10-23 14:14:23',1,'2026-10-23 14:14:23','ROTACION'),(113,1,'39d37677a17d0d84ec01a4c60690164507580a88d5a194326d4618c62e5828b9','2026-10-30 14:14:23',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:14:23',1,NULL,NULL),(114,1,'4533fa323128154046c3c4c57cb5b97d3c72ee58ce99fc7b897ce4946bfa9dda','2026-10-30 14:14:26',1,'127.0.0.1','node','2026-10-23 14:14:26',1,'2026-10-23 14:14:27','ROTACION'),(115,1,'43ecdbd35684084bdbc377b2df85a43978271272ebee9f73e1e714dd4dcd718d','2026-10-30 14:14:27',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:14:27',1,NULL,NULL),(116,1,'157412ce952917f54ace097d8d5f26a68987228d13ea01af174ddf50224f283c','2026-10-30 14:14:30',1,'127.0.0.1','node','2026-10-23 14:14:30',1,'2026-10-23 14:14:30','ROTACION'),(117,1,'ecfca9fbf802c6bee2564ace6cc4c3408d08a9a821c442936bb18cac3e6c4feb','2026-10-30 14:14:30',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:14:30',1,NULL,NULL),(118,1,'628643dde32496f7cd4be6c0dc6fed897734bcc2d3f47b1880dbc992ddcbc5d0','2026-10-30 14:14:36',1,'127.0.0.1','node','2026-10-23 14:14:36',1,'2026-10-23 14:14:36','ROTACION'),(119,1,'606a227ace678b32ffdde6c6ea24b4038377757f08a07c193002f55dc16bd017','2026-10-30 14:14:36',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:14:36',1,NULL,NULL),(120,1,'846303b7401a274ada0e84a47c2427dff5c5ec227aed7cee5524f7a96abe8281','2026-10-30 14:14:39',1,'127.0.0.1','node','2026-10-23 14:14:39',1,'2026-10-23 14:14:39','ROTACION'),(121,1,'1d9cb154487a76601df2d8564f1d2535792f6883263698ec58afd86650cb51f6','2026-10-30 14:14:39',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:14:39',1,NULL,NULL),(122,1,'a83362a7bb9583234f6f456c030d941ca0cf4dda90de6aa63edff696196ccc13','2026-10-30 14:14:42',1,'127.0.0.1','node','2026-10-23 14:14:42',1,'2026-10-23 14:14:42','ROTACION'),(123,1,'46ae12e25d33cc8d5877f5d4616a7573e989039b7fa51068d7ad9b580d575720','2026-10-30 14:14:42',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:14:42',1,NULL,NULL),(124,1,'32d60f15d0134a04437d1b70d3a3d4ed1fd83ce2ecc2616a0448b891233a1350','2026-10-30 14:14:45',1,'127.0.0.1','node','2026-10-23 14:14:45',1,'2026-10-23 14:14:45','ROTACION'),(125,1,'b81ad945075f4526d67faa27662d58b676b688e965293e74cd4e6e00ab5e78a7','2026-10-30 14:14:45',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:14:45',1,NULL,NULL),(126,1,'18ad2e23c25fca850bcbcc3611f1ac624981cc179cf2d5c11837b10c8320c7ce','2026-10-30 14:16:14',1,'127.0.0.1','node','2026-10-23 14:16:14',1,'2026-10-23 14:16:14','ROTACION'),(127,1,'00d94c97a15725bbedaf126e580a1dd09679a90148c958bf174b6188eff2fb4d','2026-10-30 14:16:14',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:16:14',1,NULL,NULL),(128,1,'6cf3a479ae745c557eca99071f5288d11e0f3f28bf01480e3f66518291cc9731','2026-10-30 14:16:17',1,'127.0.0.1','node','2026-10-23 14:16:17',1,'2026-10-23 14:16:17','ROTACION'),(129,1,'9d19bdbbecb100ec971d3ba75d4b17c6f9cecfe7914298d7fc00a33c8c742915','2026-10-30 14:16:17',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:16:17',1,NULL,NULL),(130,1,'d904e1e06e3d7d2251832d7f861c6da303330600d2f86197dc3fc5731211a4cd','2026-10-30 14:16:20',1,'127.0.0.1','node','2026-10-23 14:16:20',1,'2026-10-23 14:16:20','ROTACION'),(131,1,'e438ba5f93dd6789b6c1be503c0656c06c57ca896363806dfe8bb441e639d7ba','2026-10-30 14:16:20',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:16:20',1,NULL,NULL),(132,1,'d77d9b5925a6324277fdef2c3bd70fbf29a4935b5097dd163c5e26fe5f1ae386','2026-10-30 14:16:26',1,'127.0.0.1','node','2026-10-23 14:16:26',1,'2026-10-23 14:16:26','ROTACION'),(133,1,'3233988538c2c37f49ddfaa5b23be3d7a33509941410356ad3f41bbf39d60826','2026-10-30 14:16:26',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:16:26',1,NULL,NULL),(134,1,'cd16df03fb52e42e2c8c70cd9aff06f43a5668e53044b5fa3ee6a9c41b1a9f68','2026-10-30 14:16:29',1,'127.0.0.1','node','2026-10-23 14:16:29',1,'2026-10-23 14:16:29','ROTACION'),(135,1,'576c521c68ceb53b05da0b691386baa05be980e1ecf48c6a6f83fad3cc3d78e1','2026-10-30 14:16:30',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:16:30',1,NULL,NULL),(136,1,'c6b0dba56b289b896f0b09bf417a023d06472c60836f7fe06d65d19626ac0f52','2026-10-30 14:16:32',1,'127.0.0.1','node','2026-10-23 14:16:32',1,'2026-10-23 14:16:33','ROTACION'),(137,1,'e152f1e3fcb98a4280fa74210fab22aa72d6e8ed91777db96e2f2acc2a2b2a19','2026-10-30 14:16:33',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:16:33',1,NULL,NULL),(138,1,'4cc3604174d9a8b42b43cb6e453f307335e2a6b60204b7c40c1ac49c240922e4','2026-10-30 14:17:18',1,'127.0.0.1','node','2026-10-23 14:17:18',1,'2026-10-23 14:17:19','ROTACION'),(139,1,'39f7ea1af96403e8dee4e4388a9e7d244720c8a12ecdb0ae87e63b590a8b8c56','2026-10-30 14:17:19',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:17:19',1,NULL,NULL),(140,1,'456ce84d567113cc6d573c539a3b7dd392169d8cf0a114e48f5711971e9db35b','2026-10-30 14:17:21',1,'127.0.0.1','node','2026-10-23 14:17:21',1,'2026-10-23 14:17:22','ROTACION'),(141,1,'4e27d903eaa8d1e61636e32d248233b6445333f09ce5e302e11d575463945d32','2026-10-30 14:17:22',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:17:22',1,NULL,NULL),(142,1,'6227b14c97d0532bdb57e1fa885d2ea15430d32c02f4f8f0e4fce77ba50a2fd0','2026-10-30 14:18:26',1,'127.0.0.1','python-httpx/0.28.1','2026-10-23 14:18:26',1,'2026-10-23 14:18:26','ROTACION'),(143,1,'a3098733c33295da97fc7e961962c06ea81a87db76cb4e95e6f7e86312f3baa7','2026-10-30 14:18:26',1,'127.0.0.1','python-httpx/0.28.1','2026-10-23 14:18:26',1,'2026-10-23 14:18:26','LOGOUT'),(144,1,'1cb2686dd1166e0ae68735f363f5e236e7160be61f822fe7c7bc4b604d19427f','2026-10-30 14:18:26',1,'127.0.0.1','node','2026-10-23 14:18:26',1,'2026-10-23 14:18:27','ROTACION'),(145,1,'e5836f9a4a01a57f9877bd0b839a78de14f0345e542e0e74bb67857f845adf7a','2026-10-30 14:18:27',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 14:18:27',1,NULL,NULL),(146,1,'0deeca48ab4ae650b63b5179cb5afb20d60cb53138361e7b9287f1cfe1f0a11e','2026-10-30 14:59:25',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 14:59:25',1,'2026-10-23 15:19:43','ROTACION'),(147,1,'1fb760e49f2c8e2a1b7cc7e9d82e67a30a116b729873e1bf6a7eb2a8bd038919','2026-10-30 15:19:43',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 15:19:43',1,'2026-10-23 15:46:07','ROTACION'),(148,1,'ec3c2e5c5391dc9c29b0149e48a4afc066bd2028aa72c6c6376da1dcc9cf24ec','2026-10-30 15:21:04',0,'127.0.0.1','node','2026-10-23 15:21:04',1,NULL,NULL),(149,1,'4f58dc09bbdd96a85d515c499ad00f243e004c5f1e2b39a5718606df5d37d081','2026-10-30 15:23:31',1,'127.0.0.1','python-httpx/0.28.1','2026-10-23 15:23:31',1,'2026-10-23 15:23:31','ROTACION'),(150,1,'f3076827d5f5584f9137eeb2d8ee286faeabcbb9a819fa9433681f77255b7ab3','2026-10-30 15:23:31',1,'127.0.0.1','python-httpx/0.28.1','2026-10-23 15:23:31',1,'2026-10-23 15:23:31','LOGOUT'),(151,1,'fb293ac62b7593819e6d0554650e8279d27f73c0478c20ce93e13e8c887ee5a1','2026-10-30 15:46:07',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 15:46:07',1,'2026-10-23 16:22:46','ROTACION'),(152,1,'7c298c8583d2bc8c5e63892e8ed8033a38df6488f104f6e09634438790ba1259','2026-10-30 16:21:12',0,'127.0.0.1','python-httpx/0.28.1','2026-10-23 16:21:12',1,NULL,NULL),(153,1,'e6ba090375810ea40c336a90c7058dc28857a8a5b71bde354c3f0acb4dff5cf4','2026-10-30 16:22:46',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 16:22:46',1,'2026-10-23 16:23:06','ROTACION'),(154,1,'24538d01d6ef750691fecd18c9424a2ea34c531e41f5bf6a225ca5b6d7065c31','2026-10-30 16:23:06',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 16:23:06',1,'2026-10-23 20:27:47','ROTACION'),(155,1,'f04fbd77312fe8604c7fbe82ac8b29e540451e8782705562ac8515ddae7f0175','2026-10-30 16:27:11',1,'127.0.0.1','node','2026-10-23 16:27:11',1,'2026-10-23 16:27:12','ROTACION'),(156,1,'b03bc6bd5a7089e872b7670be6470bc87986b259656b5578db1553dcf148e58d','2026-10-30 16:27:12',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 16:27:12',1,NULL,NULL),(157,1,'0b149520551e5f456c72afa16a7cde29d1d59d43b56edaf8c219d66e4b398049','2026-10-30 16:27:14',1,'127.0.0.1','node','2026-10-23 16:27:14',1,'2026-10-23 16:27:20','ROTACION'),(158,1,'86992f8d54c7648ab0b544369d011de3f319db7c8c73cc862be5230a00433217','2026-10-30 16:27:20',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 16:27:20',1,NULL,NULL),(159,1,'2671e8f88e2caf59e06defe0efaa2f0ef016f07bf063891bb94cd6a45d2d0c6b','2026-10-30 16:28:47',0,'127.0.0.1','python-httpx/0.28.1','2026-10-23 16:28:47',1,NULL,NULL),(160,1,'38b77b2f47d499e967e40c314131479ebf9aa4483e67f6ebaff4afeef856cf17','2026-10-30 20:27:47',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 20:27:47',1,'2026-10-23 22:20:59','ROTACION'),(161,1,'8d6f158a70b73c12b1c170645f83be59a79fa1d7368ce3c2a572698bdbc239a2','2026-10-30 20:29:12',1,'127.0.0.1','node','2026-10-23 20:29:12',1,'2026-10-23 20:29:12','ROTACION'),(162,1,'33edb595db663c4d68ab81e85b0157f4e945667fd1111173acdd612429759fde','2026-10-30 20:29:12',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:12',1,NULL,NULL),(163,1,'6e08b5c8169eb785923434b27d2ff83705564683e2b10158f048ca4044d91084','2026-10-30 20:29:15',1,'127.0.0.1','node','2026-10-23 20:29:15',1,'2026-10-23 20:29:15','ROTACION'),(164,1,'e44ffeff4ea3a52efc3a2e4eccb73b2ed93279b3f06661a28cfce1cad9c5733d','2026-10-30 20:29:15',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:15',1,NULL,NULL),(165,1,'f78c70290c2660f6eeb69b270ea520c56db77330f68c71e892a294617d95ee94','2026-10-30 20:29:18',1,'127.0.0.1','node','2026-10-23 20:29:18',1,'2026-10-23 20:29:18','ROTACION'),(166,1,'14f597ba2373d3ff54f1a82b7c54a53b523930706631eabd0dc123c7d7a12d3d','2026-10-30 20:29:18',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:18',1,NULL,NULL),(167,1,'e679d6cd73265c34f0d120e1394a5bee6f438e171f060b1b7185893a665a0b84','2026-10-30 20:29:21',1,'127.0.0.1','node','2026-10-23 20:29:21',1,'2026-10-23 20:29:22','ROTACION'),(168,1,'10af1605ccf80ec6d0adafaeb7dd824a9ea871fa0e0e85b1de7cb718aabd35ae','2026-10-30 20:29:22',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:22',1,NULL,NULL),(169,1,'a92986556591ed2fb304d55711dc2b429c13006eec054195e777372d395ffe1d','2026-10-30 20:29:24',1,'127.0.0.1','node','2026-10-23 20:29:24',1,'2026-10-23 20:29:25','ROTACION'),(170,1,'9266bf85e3a3cb190a49a4b27ec7487c8ca11914f5b8a3c53594e23da0d76b4b','2026-10-30 20:29:25',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:25',1,NULL,NULL),(171,1,'7dbba52736cabd5a879f6cd3eab30225df7c783f7f02b379d6abc0897a437f70','2026-10-30 20:29:28',1,'127.0.0.1','node','2026-10-23 20:29:28',1,'2026-10-23 20:29:28','ROTACION'),(172,1,'7993d5b64644b27f82b2696aba58626d1f6b58f5315b7c13041c6745840270fd','2026-10-30 20:29:28',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:28',1,NULL,NULL),(173,1,'791869852d6945b5b33874bbc01c5ef217ca5fca31bb8d2f18c12c2394bc6208','2026-10-30 20:29:31',1,'127.0.0.1','node','2026-10-23 20:29:31',1,'2026-10-23 20:29:32','ROTACION'),(174,1,'6b88c6590b517bf15e7084e2eb77d3ab010bd6d2fe1c75ffb068f1bb3634ab2c','2026-10-30 20:29:32',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:32',1,NULL,NULL),(175,1,'a128697dd731420a53a8ba7d3cc1fcc3e0f8a4b0ed01e63a7ceb4fdc93ef42a6','2026-10-30 20:29:34',1,'127.0.0.1','node','2026-10-23 20:29:34',1,'2026-10-23 20:29:35','ROTACION'),(176,1,'765da37eed6173d373979275a4664b8d8a3878dfcb781d2c607450a7813aee2e','2026-10-30 20:29:35',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:35',1,NULL,NULL),(177,1,'54a74bea03c6645283886d7039574053e523540d69d7e41cb985bf3b71fbd6ce','2026-10-30 20:29:38',1,'127.0.0.1','node','2026-10-23 20:29:38',1,'2026-10-23 20:29:38','ROTACION'),(178,1,'c37ce3957964760b074dd182b2532c782dce3ff28d67acbe6850e2abbbbdf45a','2026-10-30 20:29:38',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:38',1,NULL,NULL),(179,1,'ae61e59c6e3c8e488a9eaf459b745ae8d9416f0d4dd6e6e67c8e973e921b5e1b','2026-10-30 20:29:41',1,'127.0.0.1','node','2026-10-23 20:29:41',1,'2026-10-23 20:29:42','ROTACION'),(180,1,'f68f911f1404a980e32f7f6fba7dc26930c7fddef7af44114b3ecbfd555f7db8','2026-10-30 20:29:42',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:29:42',1,NULL,NULL),(181,1,'6e61ebc73fa99ef4dd8effb2ee56b53b8442f3f07eaa0f5f236c0b60262d162c','2026-10-30 20:30:51',1,'127.0.0.1','node','2026-10-23 20:30:51',1,'2026-10-23 20:30:52','ROTACION'),(182,1,'7e587aba4e8c2834e822b228cc987864b0422649a73ec0f0347995b2a51bdde3','2026-10-30 20:30:52',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:30:52',1,NULL,NULL),(183,1,'67fe8238fdd286ee643cc323ad9419aaf0d0641dbca8e68fb72c635e688b8234','2026-10-30 20:31:38',1,'127.0.0.1','node','2026-10-23 20:31:38',1,'2026-10-23 20:31:38','ROTACION'),(184,1,'8cb4f7f0c5a876320e9253714a6cb3163f3060d4754ad40a9b3b6dec82298f6d','2026-10-30 20:31:38',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:31:38',1,NULL,NULL),(185,1,'88ea59a6f1c9c94880e2bd15eee6362929cd0f3f7774ca741b49604a1abcd063','2026-10-30 20:31:41',1,'127.0.0.1','node','2026-10-23 20:31:41',1,'2026-10-23 20:31:41','ROTACION'),(186,1,'8a2ab3d14706a8ab7fbace862dcf37a6ea5cc14e3a4e289dddb71af8f37a62f1','2026-10-30 20:31:41',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:31:41',1,NULL,NULL),(187,1,'c45330952b54c86d9b9c76363e56a5eac1444511a2e46e20ad179dffdf119562','2026-10-30 20:31:44',1,'127.0.0.1','node','2026-10-23 20:31:44',1,'2026-10-23 20:31:44','ROTACION'),(188,1,'e91cac456ca5be7116f856ab4eb0138e97ae908c45aeb0fa543394f299384eb2','2026-10-30 20:31:44',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:31:44',1,NULL,NULL),(189,1,'18680476bc4932142b55efebb4835228b78031e1b40b8c61bef2a60ce919bea3','2026-10-30 20:32:30',1,'127.0.0.1','node','2026-10-23 20:32:30',1,'2026-10-23 20:32:30','ROTACION'),(190,1,'7d3571565b8b5b2a3a0df6728d33e98ae86b7a1dca7624d1e4a9b7c4d754be85','2026-10-30 20:32:30',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:32:30',1,NULL,NULL),(191,1,'bd576d9c9d15726ab09ab5258c298e4f9bef5c338a533c0f295f8b6731513949','2026-10-30 20:34:05',1,'127.0.0.1','node','2026-10-23 20:34:05',1,'2026-10-23 20:34:06','ROTACION'),(192,1,'704cbca3bb279963979d330086ac73469d91205287c191d84bf120d79e30dcfa','2026-10-30 20:34:06',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:34:06',1,NULL,NULL),(193,1,'0c9331bb4c9a10fdeedeeb56b9b1df3863f24278e384d9a4c50388e35685662c','2026-10-30 20:34:09',1,'127.0.0.1','node','2026-10-23 20:34:09',1,'2026-10-23 20:34:09','ROTACION'),(194,1,'0c3ab591e468434523b7b86750606f7fbc41f15a6ac0d989fda300c8a2eea84b','2026-10-30 20:34:09',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 20:34:09',1,NULL,NULL),(195,1,'edd6b3fdcfc57010ad77571f7c55ae508fbde6777a84381d28b6c88ec86e6940','2026-10-30 22:20:59',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 22:20:59',1,'2026-10-23 22:21:58','ROTACION'),(196,1,'88f14ec3e2372ccffb9bfcccb488270056f86487fec312dc0ee45dc9f9f0a00f','2026-10-30 22:21:58',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 22:21:58',1,'2026-10-23 22:22:58','ROTACION'),(197,1,'5a6d532e6559d90976bdaf49ee1db21b2e8dcbff3defe4435c9a707ba0546085','2026-10-30 22:22:58',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 22:22:58',1,'2026-10-23 22:23:58','ROTACION'),(198,1,'3fe3e3ad2aa2484c8dfab25ef9cf879e5420a2220132464006350f03c4272573','2026-10-30 22:23:58',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 22:23:58',1,'2026-10-23 22:24:58','ROTACION'),(199,1,'e3086362bc399f9239875eacca4a56d168cd0cd133e9cbf1cc41e35190d15ba1','2026-10-30 22:24:58',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 22:24:58',1,'2026-10-23 22:25:58','ROTACION'),(200,1,'c537fb9c7c15e0f6f608b39bd1dfbeeb69de52d829233095af645bb64d02a3f5','2026-10-30 22:25:58',1,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 22:25:58',1,'2026-10-23 22:26:19','ROTACION'),(201,1,'5e61ac2392fd40bd2eccc720afd3473878380b85ca9a618fb9f0b535ea8c3b63','2026-10-30 22:26:19',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36','2026-10-23 22:26:19',1,NULL,NULL),(202,1,'ee3e63c8b2fcf5ad48254490a99afd26607a48349b0203fa59d088fd1396123c','2026-10-30 22:28:16',0,'127.0.0.1','python-httpx/0.28.1','2026-10-23 22:28:16',1,NULL,NULL),(203,1,'4bdf3e2f25fd7712a28bcb3f197d5e13f2649721f8fa3031de62fc00cfc3529f','2026-10-30 22:28:23',0,'127.0.0.1','node','2026-10-23 22:28:23',1,NULL,NULL),(204,1,'1e6df610daa742b2d57f000cfd39704e2387b3dcb6e9cbd3746e79f6e417ede5','2026-10-30 22:28:28',1,'127.0.0.1','node','2026-10-23 22:28:28',1,'2026-10-23 22:28:32','ROTACION'),(205,1,'943d689bdb6b518c05253adddae63a02799d7655d6ce4f4b9175b38407f68243','2026-10-30 22:28:32',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:28:32',1,NULL,NULL),(206,1,'46575113777a8d4202108e8ba7c0d5225dea270b46402b237a92fcf7fbe0b205','2026-10-30 22:28:34',1,'127.0.0.1','node','2026-10-23 22:28:34',1,'2026-10-23 22:28:36','ROTACION'),(207,1,'01c8e2fb5647850efd04760c1cbcf69fc3ce1cffe1a4606f95d8f6305f6db452','2026-10-30 22:28:36',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:28:36',1,NULL,NULL),(208,1,'58d7c2341a6ba7b3f795d066d649cfa7a3be573672c569a4e6e7cf17bf990645','2026-10-30 22:28:38',1,'127.0.0.1','node','2026-10-23 22:28:38',1,'2026-10-23 22:28:39','ROTACION'),(209,1,'ddc48deba4eb4d3c8ed0b8156166089f5dbfca8d5f16b86499d9fd3ed55885a4','2026-10-30 22:28:39',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:28:39',1,NULL,NULL),(210,1,'f58f131842542026ef10e59e9a68b9fd409eead63a7cea39905fc7d195fc65f5','2026-10-30 22:28:42',1,'127.0.0.1','node','2026-10-23 22:28:42',1,'2026-10-23 22:28:43','ROTACION'),(211,1,'cf44eda7be5e4f3590a48490cc2c4b4cfd0ced3158b52f8db429a2dfeee6fa65','2026-10-30 22:28:43',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:28:43',1,NULL,NULL),(212,1,'dfa6b38ccb6d5620401d5360df1396039245c070b69a27dcfc26daab509357a0','2026-10-30 22:28:46',1,'127.0.0.1','node','2026-10-23 22:28:46',1,'2026-10-23 22:28:48','ROTACION'),(213,1,'3f70bb0169e3c45ea3c7b327905b967e93132fdf29c2faff4f101f0decb537fe','2026-10-30 22:28:48',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:28:48',1,NULL,NULL),(214,1,'8a9a81f0e00b050fd958a727a513bf46ef66d48ed43e5c18c69f23f446171d4f','2026-10-30 22:28:51',1,'127.0.0.1','node','2026-10-23 22:28:51',1,'2026-10-23 22:28:52','ROTACION'),(215,1,'69081159b0ee4de4e154e6a74a2f1361e8c7142385d9eb90a3c31b5298e77ed9','2026-10-30 22:28:52',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:28:52',1,NULL,NULL),(216,1,'6d376240ab35679229f0db559ead8894b4b8a114e730437eada8d7a48a2e122f','2026-10-30 22:30:08',1,'127.0.0.1','node','2026-10-23 22:30:08',1,'2026-10-23 22:30:09','ROTACION'),(217,1,'cc03850ce60917f48f8087aa44103c236ac5ce73a425245a2ad6967ca3f0bda4','2026-10-30 22:30:09',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:30:09',1,NULL,NULL),(218,1,'da90f0ee73a2f6764f31ca634f9aa2267a01d1cbc87cdbe8ce9dd430fe3c06b7','2026-10-30 22:31:32',1,'127.0.0.1','node','2026-10-23 22:31:32',1,'2026-10-23 22:31:33','ROTACION'),(219,1,'6b9fa07df3f5a545e32d5e62004a5803073ce2058831aedf6f9a857f7341f793','2026-10-30 22:31:33',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:31:33',1,NULL,NULL),(220,1,'a432e0b20602da8b8a30bdb117856713eb5767346cb5cfbf453e24fc52ed4794','2026-10-30 22:32:18',1,'127.0.0.1','node','2026-10-23 22:32:18',1,'2026-10-23 22:32:19','ROTACION'),(221,1,'5bfd8dbd7c6cd7b043d049833ad0726ee46f34fc1c37d0e1a2a3c23f36bd9393','2026-10-30 22:32:19',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:32:19',1,NULL,NULL),(222,1,'d62f0f6b7809a046082e11e58cfaeefca35a71ae616c366efd7270a04673b49e','2026-10-30 22:36:47',1,'127.0.0.1','node','2026-10-23 22:36:47',1,'2026-10-23 22:36:47','ROTACION'),(223,1,'39bc512cb084df037a782bb108b1a31021ef2fd0d4ac5e8f989ef007f2f6da2b','2026-10-30 22:36:47',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:36:47',1,NULL,NULL),(224,1,'1963423457f89002cbd3f09d4547ae8d375b16af08a253888fc9a58bd55bc17d','2026-10-30 22:39:27',1,'127.0.0.1','node','2026-10-23 22:39:27',1,'2026-10-23 22:39:28','ROTACION'),(225,1,'69de0cb739908e09e5f3bcb5d5d577b862d05edcec95fbeb01dc6ddc698b8bad','2026-10-30 22:39:28',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:39:28',1,NULL,NULL),(226,1,'f9df888673f5e2ae96e7077d0c791479f4e1cfad1140558da94911f142554365','2026-10-30 22:39:31',1,'127.0.0.1','node','2026-10-23 22:39:31',1,'2026-10-23 22:39:31','ROTACION'),(227,1,'4b171cea17bf251b4c40367e974f6e416ef578f9e482ef7d76013bfda88c641a','2026-10-30 22:39:31',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:39:31',1,NULL,NULL),(228,1,'c0a891807590897ba90a7e768330d2cc1f34d0f2054fb6e8d59bbd90d4e0fac3','2026-10-30 22:39:34',1,'127.0.0.1','node','2026-10-23 22:39:34',1,'2026-10-23 22:39:34','ROTACION'),(229,1,'56a368bc54a674521a6bf161d63b24aaa50bc41cc558fdf8eb5d25801a0287ff','2026-10-30 22:39:34',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:39:34',1,NULL,NULL),(230,1,'c7283cfef3b087de3a2b46f1b8079b3e1947c95060cdfd410be02c0860c6668b','2026-10-30 22:39:37',1,'127.0.0.1','node','2026-10-23 22:39:37',1,'2026-10-23 22:39:37','ROTACION'),(231,1,'704d18292d3ab0ff803a27e977c1a82acffc06c385665275826ae4656d5c655a','2026-10-30 22:39:37',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:39:37',1,NULL,NULL),(232,1,'757ec9c89316bfd6a4c842bf7cba26b09d69c4c8f0a6c263fc5b6eea838e6f85','2026-10-30 22:41:00',1,'127.0.0.1','node','2026-10-23 22:41:00',1,'2026-10-23 22:41:01','ROTACION'),(233,1,'311a2b18d2e4de8635d8747b1bce7217ced8b687bd99989d5131d53aaa156984','2026-10-30 22:41:01',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:41:01',1,NULL,NULL),(234,1,'1675ccf6ebf052eca22ee2949f56aa036e7858b4b8cf3135c41d9c0d8ac0c035','2026-10-30 22:42:04',1,'127.0.0.1','node','2026-10-23 22:42:04',1,'2026-10-23 22:42:04','ROTACION'),(235,1,'c043f062c1970faa68b77bce137de3b6ee78ad5aba5f4eafb33347e1486b9bac','2026-10-30 22:42:04',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:42:04',1,NULL,NULL),(236,1,'66ca97ecc6672261872bc218604e252e08ab60a9929199565995f9ccc1d65c5a','2026-10-30 22:48:59',1,'127.0.0.1','node','2026-10-23 22:48:59',1,'2026-10-23 22:48:59','ROTACION'),(237,1,'a1d1d652cd2d688fce5ee5137cd98463fb72e2ee2fa05253d9d675265f413357','2026-10-30 22:48:59',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:48:59',1,NULL,NULL),(238,1,'da8262e009e9661bf31eeaf839ba1afc11b54c444f21dfba8b27c6b362878a98','2026-10-30 22:49:02',1,'127.0.0.1','node','2026-10-23 22:49:02',1,'2026-10-23 22:49:02','ROTACION'),(239,1,'10ae1dd46a9a52179a2dda0645f98828827e519b14171dbf6ca7f6ec4d5aa1dd','2026-10-30 22:49:02',0,'127.0.0.1','Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/155.0.0.0 Safari/537.36','2026-10-23 22:49:02',1,NULL,NULL);
/*!40000 ALTER TABLE `refresh_tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `resumen_cierre_caja`
--

DROP TABLE IF EXISTS `resumen_cierre_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `resumen_cierre_caja` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sesion_caja_id` int NOT NULL,
  `metodo` varchar(30) NOT NULL,
  `cantidad_operaciones` int NOT NULL,
  `monto_sistema` decimal(12,2) NOT NULL,
  `monto_declarado` decimal(12,2) DEFAULT NULL,
  `diferencia` decimal(12,2) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_resumen_cierre_caja_sesion_caja_id_metodo` (`sesion_caja_id`,`metodo`),
  CONSTRAINT `fk_resumen_cierre_caja_sesion_caja_id_sesiones_caja` FOREIGN KEY (`sesion_caja_id`) REFERENCES `sesiones_caja` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `resumen_cierre_caja`
--

LOCK TABLES `resumen_cierre_caja` WRITE;
/*!40000 ALTER TABLE `resumen_cierre_caja` DISABLE KEYS */;
/*!40000 ALTER TABLE `resumen_cierre_caja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rol_permisos`
--

DROP TABLE IF EXISTS `rol_permisos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `rol_permisos` (
  `rol_id` int NOT NULL,
  `permiso_id` int NOT NULL,
  PRIMARY KEY (`rol_id`,`permiso_id`),
  KEY `fk_rol_permisos_permiso_id_permisos` (`permiso_id`),
  CONSTRAINT `fk_rol_permisos_permiso_id_permisos` FOREIGN KEY (`permiso_id`) REFERENCES `permisos` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_rol_permisos_rol_id_roles` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rol_permisos`
--

LOCK TABLES `rol_permisos` WRITE;
/*!40000 ALTER TABLE `rol_permisos` DISABLE KEYS */;
INSERT INTO `rol_permisos` VALUES (1,1),(2,1),(3,1),(1,2),(2,2),(1,3),(1,4),(2,4),(1,5),(1,6),(1,7),(2,7),(1,8),(2,8),(1,9),(2,9),(1,10),(2,10),(1,11),(1,12),(2,12),(3,12),(1,13),(3,13),(1,14),(3,14),(1,15),(1,16),(3,16),(1,17),(3,17),(1,18),(2,18),(3,18),(1,19),(3,19),(1,20),(3,20),(1,21),(1,22),(2,22),(3,22),(1,23),(3,23),(1,24),(3,24),(1,25),(1,26),(2,26),(3,26),(1,27),(3,27),(1,28),(3,28),(1,29),(1,30),(3,30),(1,31),(3,31),(1,32),(2,32),(3,32),(1,33),(3,33),(1,34),(1,35),(1,36),(3,36),(1,37),(3,37),(1,38),(3,38),(1,39),(1,40),(3,40),(1,41),(3,41),(1,42),(3,42),(1,43),(1,44),(1,45),(2,45),(1,46),(2,46),(1,47),(1,48),(1,49),(2,49),(1,50),(1,51),(1,52),(1,53),(1,54),(1,55),(1,56),(1,57),(1,58),(1,59),(1,60),(1,61),(1,62),(1,63),(1,64);
/*!40000 ALTER TABLE `rol_permisos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `descripcion` varchar(200) DEFAULT NULL,
  `es_sistema` tinyint(1) NOT NULL DEFAULT '0',
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_roles_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES (1,'Administrador','Acceso total al sistema',1,1,'2026-10-22 22:00:50','2026-10-22 22:00:50'),(2,'Cajero','Ventas, caja y atención de clientes',1,1,'2026-10-22 22:00:50','2026-10-22 22:00:50'),(3,'Almacenero','Productos, inventario, proveedores y compras',1,1,'2026-10-22 22:00:50','2026-10-22 22:00:50');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `series_comprobante`
--

DROP TABLE IF EXISTS `series_comprobante`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `series_comprobante` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sucursal_id` int NOT NULL,
  `tipo_comprobante` varchar(30) NOT NULL,
  `serie` varchar(4) NOT NULL,
  `correlativo_actual` int NOT NULL DEFAULT '0',
  `predeterminada` tinyint(1) NOT NULL DEFAULT '0',
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `predeterminada_clave` varchar(45) GENERATED ALWAYS AS ((case when `predeterminada` then concat(`sucursal_id`,_utf8mb4'-',`tipo_comprobante`) end)) STORED,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_series_comprobante_serie` (`serie`),
  UNIQUE KEY `uq_series_comprobante_predeterminada_clave` (`predeterminada_clave`),
  KEY `ix_series_comprobante_sucursal_id` (`sucursal_id`),
  CONSTRAINT `fk_series_comprobante_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_series_comprobante_correlativo_no_negativo` CHECK ((`correlativo_actual` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `series_comprobante`
--

LOCK TABLES `series_comprobante` WRITE;
/*!40000 ALTER TABLE `series_comprobante` DISABLE KEYS */;
INSERT INTO `series_comprobante` (`id`, `sucursal_id`, `tipo_comprobante`, `serie`, `correlativo_actual`, `predeterminada`, `activo`, `creado_en`, `actualizado_en`) VALUES (1,1,'TICKET','T001',4,1,1,'2026-10-22 22:00:50','2026-10-23 22:42:09'),(2,1,'BOLETA','B001',0,1,1,'2026-10-22 22:00:50','2026-10-22 22:00:50'),(3,1,'FACTURA','F001',0,1,1,'2026-10-22 22:00:50','2026-10-22 22:00:50');
/*!40000 ALTER TABLE `series_comprobante` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sesiones_caja`
--

DROP TABLE IF EXISTS `sesiones_caja`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sesiones_caja` (
  `id` int NOT NULL AUTO_INCREMENT,
  `caja_id` int NOT NULL,
  `usuario_id` int NOT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'ABIERTA',
  `monto_inicial` decimal(12,2) NOT NULL,
  `fecha_apertura` datetime NOT NULL DEFAULT (now()),
  `fecha_cierre` datetime DEFAULT NULL,
  `monto_esperado` decimal(12,2) DEFAULT NULL,
  `monto_contado` decimal(12,2) DEFAULT NULL,
  `diferencia` decimal(12,2) DEFAULT NULL,
  `observaciones_apertura` varchar(300) DEFAULT NULL,
  `observaciones_cierre` varchar(300) DEFAULT NULL,
  `usuario_abierta_id` int GENERATED ALWAYS AS ((case when (`estado` = _utf8mb4'ABIERTA') then `usuario_id` end)) STORED,
  `caja_abierta_id` int GENERATED ALWAYS AS ((case when (`estado` = _utf8mb4'ABIERTA') then `caja_id` end)) STORED,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sesiones_caja_caja_abierta_id` (`caja_abierta_id`),
  UNIQUE KEY `uq_sesiones_caja_usuario_abierta_id` (`usuario_abierta_id`),
  KEY `fk_sesiones_caja_caja_id_cajas` (`caja_id`),
  KEY `ix_sesiones_caja_estado` (`estado`),
  KEY `ix_sesiones_caja_fecha_apertura` (`fecha_apertura`),
  KEY `ix_sesiones_caja_fecha_cierre` (`fecha_cierre`),
  KEY `ix_sesiones_caja_usuario_apertura` (`usuario_id`,`fecha_apertura`),
  CONSTRAINT `fk_sesiones_caja_caja_id_cajas` FOREIGN KEY (`caja_id`) REFERENCES `cajas` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_sesiones_caja_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_sesiones_caja_monto_contado_no_negativo` CHECK (((`monto_contado` is null) or (`monto_contado` >= 0))),
  CONSTRAINT `ck_sesiones_caja_monto_inicial_no_negativo` CHECK ((`monto_inicial` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sesiones_caja`
--

LOCK TABLES `sesiones_caja` WRITE;
/*!40000 ALTER TABLE `sesiones_caja` DISABLE KEYS */;
INSERT INTO `sesiones_caja` (`id`, `caja_id`, `usuario_id`, `estado`, `monto_inicial`, `fecha_apertura`, `fecha_cierre`, `monto_esperado`, `monto_contado`, `diferencia`, `observaciones_apertura`, `observaciones_cierre`, `creado_en`, `actualizado_en`) VALUES (5,1,1,'ABIERTA',100.00,'2026-10-23 22:28:16',NULL,NULL,NULL,NULL,NULL,NULL,'2026-10-23 22:28:16','2026-10-23 22:28:16');
/*!40000 ALTER TABLE `sesiones_caja` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `stock_almacen`
--

DROP TABLE IF EXISTS `stock_almacen`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `stock_almacen` (
  `id` int NOT NULL AUTO_INCREMENT,
  `producto_id` int NOT NULL,
  `almacen_id` int NOT NULL,
  `cantidad` decimal(12,3) NOT NULL DEFAULT '0.000',
  `stock_minimo` decimal(12,3) DEFAULT NULL,
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  `pendiente_lote` decimal(12,3) NOT NULL DEFAULT '0.000',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_stock_almacen_producto_id_almacen_id` (`producto_id`,`almacen_id`),
  KEY `ix_stock_almacen_almacen_producto` (`almacen_id`,`producto_id`),
  CONSTRAINT `fk_stock_almacen_almacen_id_almacenes` FOREIGN KEY (`almacen_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_stock_almacen_producto_id_productos` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_stock_almacen_pendiente_lote_no_negativo` CHECK ((`pendiente_lote` >= 0)),
  CONSTRAINT `ck_stock_almacen_stock_minimo_no_negativo` CHECK (((`stock_minimo` is null) or (`stock_minimo` >= 0)))
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `stock_almacen`
--

LOCK TABLES `stock_almacen` WRITE;
/*!40000 ALTER TABLE `stock_almacen` DISABLE KEYS */;
INSERT INTO `stock_almacen` VALUES (5,3,1,31.000,NULL,'2026-10-23 22:42:09',0.000),(6,4,1,5.000,NULL,'2026-10-23 16:20:58',0.000),(7,5,1,3.000,NULL,'2026-10-23 16:20:58',0.000),(8,6,1,40.000,NULL,'2026-10-23 16:20:58',0.000),(9,7,1,33.000,NULL,'2026-10-23 22:28:16',0.000),(10,8,1,96.000,NULL,'2026-10-23 16:20:58',0.000),(11,9,1,48.000,NULL,'2026-10-23 16:20:58',0.000),(12,10,1,36.000,NULL,'2026-10-23 16:20:58',0.000),(13,11,1,56.000,NULL,'2026-10-23 22:42:09',0.000),(14,12,1,24.000,NULL,'2026-10-23 16:20:58',0.000),(15,13,1,18.000,NULL,'2026-10-23 16:20:58',0.000),(16,14,1,12.000,NULL,'2026-10-23 16:20:58',0.000),(17,15,1,119.000,NULL,'2026-10-23 22:28:16',0.000),(18,17,1,12.000,NULL,'2026-10-23 16:20:58',0.000),(19,18,1,4.000,NULL,'2026-10-23 16:20:58',0.000),(20,19,1,10.000,NULL,'2026-10-23 16:20:58',0.000),(21,20,1,90.000,NULL,'2026-10-23 16:20:58',0.000),(22,21,1,180.000,NULL,'2026-10-23 16:20:58',0.000),(23,22,1,8.000,NULL,'2026-10-23 16:20:58',0.000),(24,23,1,22.000,NULL,'2026-10-23 16:20:58',0.000),(25,24,1,30.000,NULL,'2026-10-23 16:20:58',0.000),(26,25,1,47.000,NULL,'2026-10-23 22:42:09',0.000),(27,27,1,12.000,NULL,'2026-10-23 22:42:09',0.000),(28,28,1,20.000,NULL,'2026-10-23 16:20:58',0.000),(29,29,1,9.000,NULL,'2026-10-23 16:20:58',0.000),(30,30,1,25.000,NULL,'2026-10-23 16:20:58',0.000),(31,31,1,18.000,NULL,'2026-10-23 16:20:58',0.000),(32,32,1,15.000,NULL,'2026-10-23 16:20:58',0.000),(33,33,1,24.250,NULL,'2026-10-23 22:42:09',0.000),(34,34,1,40.250,NULL,'2026-10-23 16:20:58',0.000),(35,35,1,8.750,NULL,'2026-10-23 16:20:58',0.000),(36,36,1,5.000,NULL,'2026-10-23 16:20:58',0.000);
/*!40000 ALTER TABLE `stock_almacen` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `sucursales`
--

DROP TABLE IF EXISTS `sucursales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `sucursales` (
  `id` int NOT NULL AUTO_INCREMENT,
  `codigo` varchar(10) NOT NULL,
  `nombre` varchar(100) NOT NULL,
  `direccion` varchar(250) DEFAULT NULL,
  `telefono` varchar(20) DEFAULT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_sucursales_codigo` (`codigo`),
  UNIQUE KEY `uq_sucursales_nombre` (`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sucursales`
--

LOCK TABLES `sucursales` WRITE;
/*!40000 ALTER TABLE `sucursales` DISABLE KEYS */;
INSERT INTO `sucursales` VALUES (1,'0000','Principal','Av. Principal 123, Lima',NULL,1,'2026-10-22 22:00:50','2026-10-22 22:00:50');
/*!40000 ALTER TABLE `sucursales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `transferencias`
--

DROP TABLE IF EXISTS `transferencias`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `transferencias` (
  `id` int NOT NULL AUTO_INCREMENT,
  `numero` varchar(20) NOT NULL,
  `almacen_origen_id` int NOT NULL,
  `almacen_destino_id` int NOT NULL,
  `estado` varchar(30) NOT NULL DEFAULT 'PENDIENTE',
  `observaciones` varchar(300) DEFAULT NULL,
  `usuario_id` int NOT NULL,
  `usuario_recibe_id` int DEFAULT NULL,
  `fecha_envio` datetime DEFAULT NULL,
  `fecha_recepcion` datetime DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_transferencias_numero` (`numero`),
  KEY `fk_transferencias_usuario_id_usuarios` (`usuario_id`),
  KEY `fk_transferencias_usuario_recibe_id_usuarios` (`usuario_recibe_id`),
  KEY `ix_transferencias_destino_estado` (`almacen_destino_id`,`estado`),
  KEY `ix_transferencias_fecha_envio` (`fecha_envio`),
  KEY `ix_transferencias_origen_estado` (`almacen_origen_id`,`estado`),
  CONSTRAINT `fk_transferencias_almacen_destino_id_almacenes` FOREIGN KEY (`almacen_destino_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_transferencias_almacen_origen_id_almacenes` FOREIGN KEY (`almacen_origen_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_transferencias_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_transferencias_usuario_recibe_id_usuarios` FOREIGN KEY (`usuario_recibe_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_transferencias_origen_distinto_destino` CHECK ((`almacen_origen_id` <> `almacen_destino_id`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `transferencias`
--

LOCK TABLES `transferencias` WRITE;
/*!40000 ALTER TABLE `transferencias` DISABLE KEYS */;
/*!40000 ALTER TABLE `transferencias` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuario_sucursales`
--

DROP TABLE IF EXISTS `usuario_sucursales`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuario_sucursales` (
  `usuario_id` int NOT NULL,
  `sucursal_id` int NOT NULL,
  PRIMARY KEY (`usuario_id`,`sucursal_id`),
  KEY `fk_usuario_sucursales_sucursal_id_sucursales` (`sucursal_id`),
  CONSTRAINT `fk_usuario_sucursales_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_usuario_sucursales_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuario_sucursales`
--

LOCK TABLES `usuario_sucursales` WRITE;
/*!40000 ALTER TABLE `usuario_sucursales` DISABLE KEYS */;
INSERT INTO `usuario_sucursales` VALUES (1,1);
/*!40000 ALTER TABLE `usuario_sucursales` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `usuarios`
--

DROP TABLE IF EXISTS `usuarios`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `usuarios` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nombre_completo` varchar(150) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(150) DEFAULT NULL,
  `password_hash` varchar(100) NOT NULL,
  `rol_id` int NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  `ultimo_acceso` datetime DEFAULT NULL,
  `intentos_fallidos` int NOT NULL DEFAULT '0',
  `bloqueado_hasta` datetime DEFAULT NULL,
  `debe_cambiar_password` tinyint(1) NOT NULL DEFAULT '0',
  `password_actualizado_en` datetime DEFAULT NULL,
  `sucursal_predeterminada_id` int DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_usuarios_username` (`username`),
  UNIQUE KEY `uq_usuarios_email` (`email`),
  KEY `fk_usuarios_sucursal_predeterminada_id_sucursales` (`sucursal_predeterminada_id`),
  KEY `ix_usuarios_rol_id` (`rol_id`),
  CONSTRAINT `fk_usuarios_rol_id_roles` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_usuarios_sucursal_predeterminada_id_sucursales` FOREIGN KEY (`sucursal_predeterminada_id`) REFERENCES `sucursales` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `usuarios`
--

LOCK TABLES `usuarios` WRITE;
/*!40000 ALTER TABLE `usuarios` DISABLE KEYS */;
INSERT INTO `usuarios` VALUES (1,'Administrador del Sistema','admin','admin@minimarket.local','$2b$12$YS/HHtoWDvpPXxezuwNR8eKAnBSFXKgULrUYzvpyW84dd.4aabWjC',1,1,'2026-10-23 22:49:02',0,NULL,0,NULL,1,'2026-10-22 22:00:51','2026-10-23 22:49:02');
/*!40000 ALTER TABLE `usuarios` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ventas`
--

DROP TABLE IF EXISTS `ventas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `ventas` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `sucursal_id` int NOT NULL,
  `almacen_id` int NOT NULL,
  `tipo_comprobante` varchar(30) NOT NULL,
  `serie` varchar(4) NOT NULL,
  `numero` int NOT NULL,
  `fecha` datetime NOT NULL DEFAULT (now()),
  `sesion_caja_id` int NOT NULL,
  `usuario_id` int NOT NULL,
  `cliente_id` int DEFAULT NULL,
  `op_gravadas` decimal(12,2) NOT NULL DEFAULT '0.00',
  `op_exoneradas` decimal(12,2) NOT NULL DEFAULT '0.00',
  `op_inafectas` decimal(12,2) NOT NULL DEFAULT '0.00',
  `igv` decimal(12,2) NOT NULL DEFAULT '0.00',
  `icbper` decimal(12,2) NOT NULL DEFAULT '0.00',
  `descuento` decimal(12,2) NOT NULL DEFAULT '0.00',
  `total` decimal(12,2) NOT NULL,
  `redondeo` decimal(12,2) NOT NULL DEFAULT '0.00',
  `vuelto` decimal(12,2) NOT NULL DEFAULT '0.00',
  `total_devuelto` decimal(12,2) NOT NULL DEFAULT '0.00',
  `es_credito` tinyint(1) NOT NULL DEFAULT '0',
  `estado` varchar(30) NOT NULL DEFAULT 'COMPLETADA',
  `observaciones` varchar(300) DEFAULT NULL,
  `anulada_por_id` int DEFAULT NULL,
  `fecha_anulacion` datetime DEFAULT NULL,
  `motivo_anulacion` varchar(300) DEFAULT NULL,
  `creado_en` datetime NOT NULL DEFAULT (now()),
  `actualizado_en` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_ventas_serie_numero` (`serie`,`numero`),
  KEY `fk_ventas_almacen_id_almacenes` (`almacen_id`),
  KEY `fk_ventas_anulada_por_id_usuarios` (`anulada_por_id`),
  KEY `ix_ventas_cliente_id` (`cliente_id`),
  KEY `ix_ventas_fecha` (`fecha`),
  KEY `ix_ventas_fecha_estado` (`fecha`,`estado`),
  KEY `ix_ventas_sesion_caja_id` (`sesion_caja_id`),
  KEY `ix_ventas_sucursal_fecha_estado` (`sucursal_id`,`fecha`,`estado`),
  KEY `ix_ventas_usuario_fecha` (`usuario_id`,`fecha`),
  CONSTRAINT `fk_ventas_almacen_id_almacenes` FOREIGN KEY (`almacen_id`) REFERENCES `almacenes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ventas_anulada_por_id_usuarios` FOREIGN KEY (`anulada_por_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ventas_cliente_id_clientes` FOREIGN KEY (`cliente_id`) REFERENCES `clientes` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ventas_sesion_caja_id_sesiones_caja` FOREIGN KEY (`sesion_caja_id`) REFERENCES `sesiones_caja` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ventas_sucursal_id_sucursales` FOREIGN KEY (`sucursal_id`) REFERENCES `sucursales` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_ventas_usuario_id_usuarios` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `ck_ventas_descuento_no_negativo` CHECK ((`descuento` >= 0)),
  CONSTRAINT `ck_ventas_devuelto_valido` CHECK (((`total_devuelto` >= 0) and (`total_devuelto` <= `total`))),
  CONSTRAINT `ck_ventas_total_no_negativo` CHECK ((`total` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ventas`
--

LOCK TABLES `ventas` WRITE;
/*!40000 ALTER TABLE `ventas` DISABLE KEYS */;
INSERT INTO `ventas` VALUES (3,1,1,'TICKET','T001',1,'2026-10-23 22:28:16',5,1,NULL,6.86,0.00,0.00,1.24,0.00,0.00,8.10,0.00,41.90,0.00,0,'COMPLETADA',NULL,NULL,NULL,NULL,'2026-10-23 22:28:16','2026-10-23 22:28:16'),(4,1,1,'TICKET','T001',2,'2026-10-23 22:28:16',5,1,NULL,17.54,0.00,0.00,3.16,0.00,0.00,20.70,0.00,0.00,0.00,0,'COMPLETADA',NULL,NULL,NULL,NULL,'2026-10-23 22:28:16','2026-10-23 22:28:16'),(5,1,1,'TICKET','T001',3,'2026-10-23 22:28:16',5,1,NULL,8.05,0.00,0.00,1.45,0.00,0.00,9.50,0.00,0.00,0.00,0,'COMPLETADA',NULL,NULL,NULL,NULL,'2026-10-23 22:28:16','2026-10-23 22:28:16'),(6,1,1,'TICKET','T001',4,'2026-10-23 22:42:09',5,1,NULL,24.91,4.38,0.00,4.49,0.00,0.00,33.78,0.00,16.22,0.00,0,'COMPLETADA',NULL,NULL,NULL,NULL,'2026-10-23 22:42:09','2026-10-23 22:42:09');
/*!40000 ALTER TABLE `ventas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'minimarket'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-23 18:04:33
