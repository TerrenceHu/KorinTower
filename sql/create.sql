DROP TABLE IF EXISTS kt.groups;
CREATE TABLE kt.groups (
	id BIGINT PRIMARY KEY,
	name VARCHAR(100) NOT NULL
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;


DROP TABLE IF EXISTS kt.users;
CREATE TABLE kt.users (
	id BIGINT PRIMARY KEY,
	username VARCHAR(100),
	first_name VARCHAR(100),
	last_name VARCHAR(100),
	is_bot BOOLEAN,
	about VARCHAR(255)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;


DROP TABLE IF EXISTS kt.group_members;
CREATE TABLE kt.group_members (
	group_id BIGINT NOT NULL,
	user_id BIGINT NOT NULL,
	updated_on DATE,
	PRIMARY KEY (group_id, user_id)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;
