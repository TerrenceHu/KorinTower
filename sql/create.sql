--------------------------------
-- users
--------------------------------
DROP TABLE IF EXISTS kt.users;
CREATE TABLE kt.users (
	id BIGINT PRIMARY KEY,
	username VARCHAR(100),
	first_name VARCHAR(100),
	last_name VARCHAR(100),
	about VARCHAR(255)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS kt.user_channels;
CREATE TABLE kt.user_channels (
	user_id BIGINT NOT NULL,
	channel_id BIGINT NOT NULL,
	updated_date DATE,
	PRIMARY KEY (user_id, channel_id)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;

--------------------------------
-- groups
--------------------------------
DROP TABLE IF EXISTS kt.groups;
CREATE TABLE kt.groups (
	id BIGINT PRIMARY KEY,
	username VARCHAR(100),
	title VARCHAR(255),
	participants_count BIGINT,
	city VARCHAR(100) DEFAULT NULL,
	status INT DEFAULT 0,
	updated_date DATE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;

--------------------------------
-- channels
--------------------------------
DROP TABLE IF EXISTS kt.channels;
CREATE TABLE kt.channels (
	id BIGINT PRIMARY KEY,
	username VARCHAR(100),
	title VARCHAR(255) NOT NULL,
	about VARCHAR(255),
	type INT DEFAULT 0,
	retries INT DEFAULT 0,
	status INT DEFAULT 0,
	updated_date DATE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS kt.channel_messages;
CREATE TABLE kt.channel_messages (
	channel_id BIGINT NOT NULL,
	message_id BIGINT NOT NULL,
	message TEXT,
	pinned BOOLEAN DEFAULT FALSE,
	comments BOOLEAN DEFAULT FALSE,
	replies INT DEFAULT 0,
	reactions INT DEFAULT 0,
	views INT DEFAULT 0,
	dt DATETIME,
	PRIMARY KEY (channel_id, message_id)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;

--------------------------------
-- teachers
--------------------------------
DROP TABLE IF EXISTS kt.teachers;
CREATE TABLE kt.teachers (
	id BIGINT PRIMARY KEY,
	username VARCHAR(100),
	name VARCHAR(100),
	city_id BIGINT,
	district_id BIGINT,
	price1p VARCHAR(255),
	status INT DEFAULT 0,
	updated_date DATE,
	score FLOAT DEFAULT 0,
	INDEX idx_city_id (city_id),
	INDEX idx_district_id (district_id)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;

DROP TABLE IF EXISTS kt.teachers_info;
CREATE TABLE kt.teachers_info (
    id BIGINT PRIMARY KEY,
	age VARCHAR(100),
	price VARCHAR(255),
	height VARCHAR(100),
	weight VARCHAR(100),
	measurement VARCHAR(100),
    service VARCHAR(255),
    FOREIGN KEY (id) REFERENCES kt.teachers(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS kt.reports;
CREATE TABLE kt.reports (
    teacher_id BIGINT PRIMARY KEY,
    channel_id BIGINT NOT NULL,
    username VARCHAR(100),
    message_id BIGINT NOT NULL,
    type INT DEFAULT 0,
    status INT DEFAULT 0,
    dt DATETIME,
    FOREIGN KEY (teacher_id) REFERENCES kt.teachers(id) ON DELETE CASCADE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;

--------------------------------
-- districts
--------------------------------
DROP TABLE IF EXISTS kt.districts;  
CREATE TABLE kt.districts (  
  id BIGINT PRIMARY KEY,
  name VARCHAR(100) DEFAULT NULL,
  pid BIGINT DEFAULT NULL,
  status INT DEFAULT 0,
  KEY `idx_pid` (pid)
) ENGINE=INNODB DEFAULT CHARSET=utf8;


--------------------------------
-- visited usernames
--------------------------------
DROP TABLE IF EXISTS kt.visited_usernames;
CREATE TABLE kt.visited_usernames (
	username VARCHAR(100) PRIMARY KEY,
	visited_date DATE
)
