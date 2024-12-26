
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

----------------------------------

DROP TABLE IF EXISTS kt.groups;
CREATE TABLE kt.groups (
	id BIGINT PRIMARY KEY,
	username VARCHAR(100),
	title VARCHAR(255),
	join_request BOOLEAN,
	participants_count BIGINT,
	updated_on DATE
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

----------------------------------

DROP TABLE IF EXISTS kt.channels;
CREATE TABLE kt.channels (
	id BIGINT PRIMARY KEY,
	title VARCHAR(100) NOT NULL,
	username VARCHAR(100) NOT NULL,
	is_teacher BOOLEAN,
	UNIQUE INDEX idx_username (username)
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;
