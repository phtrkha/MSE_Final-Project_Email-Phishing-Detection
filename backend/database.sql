-- Adminer 4.8.1 MySQL 8.0.39 dump

SET NAMES utf8;
SET time_zone = '+00:00';
SET foreign_key_checks = 0;
SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO';

SET NAMES utf8mb4;

DROP TABLE IF EXISTS `email_logs`;
CREATE TABLE `email_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mailId` text,
  `createdDateTime` text,
  `lastModifiedDateTime` text,
  `receivedDateTime` text,
  `subject` text,
  `bodyPreview` text,
  `isRead` text,
  `bodyContent` longtext,
  `senderEmailAddress` text,
  `senderName` text,
  `fromEmailAddress` text,
  `fromName` text,
  `toRecipientEmailAddress` text,
  `toRecipientName` text,
  `data` longtext,
  `classification` text,
  `classifyBy` text,
  `click` text,
  `userId` text,
  `classificationOfUser` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `classifyByUser` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `classifyByManual` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  PRIMARY KEY (`id`),
  UNIQUE KEY `mailId` (`mailId`(255))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;



-- 2024-09-29 07:38:55

