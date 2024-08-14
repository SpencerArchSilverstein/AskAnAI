CREATE DATABASE IF NOT EXISTS final_project;

USE final_project;

CREATE TABLE jobs
(
    jobid             int not null AUTO_INCREMENT,
    status            varchar(256) not null,  -- uploaded, completed, error, processing...
    originaldatafile  varchar(256) not null,  -- original PDF filename from user
    txtfilekey       varchar(256) not null,  -- PDF filename in S3 (bucketkey)
    responsefilekey    varchar(256) not null,  -- results filename in S3 bucket
    PRIMARY KEY (jobid)
);

ALTER TABLE jobs AUTO_INCREMENT = 1001;  -- starting value

DROP USER IF EXISTS 'read-only';
DROP USER IF EXISTS 'read-write';

CREATE USER 'read-only' IDENTIFIED BY 'IDENTITY';
CREATE USER 'read-write' IDENTIFIED BY 'IDENTITY';

GRANT SELECT, SHOW VIEW ON final_project.* 
      TO 'read-only';
GRANT SELECT, SHOW VIEW, INSERT, UPDATE, DELETE, DROP, CREATE, ALTER ON final_project.*
      TO 'read-write';

FLUSH PRIVILEGES;