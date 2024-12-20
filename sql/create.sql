DROP TABLE IF EXISTS kt.groups;
CREATE TABLE kt.groups (
	id INT PRIMARY KEY,
	name VARCHAR(100) NOT NULL
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci;


DROP TABLE IF EXISTS kt.users;
CREATE TABLE kt.users (
	id INT PRIMARY KEY,
	name VARCHAR(100) NOT null,
	is_bot BOOLEAN,
	first_name VARCHAR(100) NOT NULL,
	last_name VARCHAR(100) NOT NULL,
	about VARCHAR(255) NOT null
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb3
COLLATE=utf8mb3_general_ci;


DROP TABLE IF EXISTS kt.group_members;
CREATE TABLE kt.group_members (
	group_id INT PRIMARY KEY,
	user_id INT,
	updated_at DATE
)
ENGINE=InnoDB
DEFAULT CHARSET=utf8mb3
COLLATE=utf8mb3_general_ci;
