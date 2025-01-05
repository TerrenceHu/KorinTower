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

--------------------------------
-- groups
--------------------------------
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

--------------------------------
-- channels
--------------------------------
DROP TABLE IF EXISTS kt.channels;
CREATE TABLE kt.channels (
	id BIGINT PRIMARY KEY,
	username VARCHAR(100),
	title VARCHAR(255) NOT NULL,
	join_request BOOLEAN,
	participants_count BIGINT,
	updated_on DATE,
	type INT DEFAULT 0
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
-- districts
--------------------------------

DROP TABLE IF EXISTS kt.districts;  
CREATE TABLE kt.districts (  
  id BIGINT PRIMARY KEY,
  name VARCHAR(100) DEFAULT NULL,
  pid BIGINT DEFAULT NULL,
  KEY `idx_pid` (pid)
) ENGINE=INNODB DEFAULT CHARSET=utf8;

INSERT INTO kt.districts VALUES (0, '中国', NULL);

INSERT INTO kt.districts VALUES (100000, '北京市', 0);
INSERT INTO kt.districts VALUES (200000, '上海市', 0);
INSERT INTO kt.districts VALUES (300000, '天津市', 0);
INSERT INTO kt.districts VALUES (400000, '重庆市', 0);

INSERT INTO kt.districts VALUES (050000, '石家庄市', 0);
INSERT INTO kt.districts VALUES (030000, '太原市', 0);
INSERT INTO kt.districts VALUES (110000, '沈阳市', 0);
INSERT INTO kt.districts VALUES (130000, '长春市', 0);
INSERT INTO kt.districts VALUES (150000, '哈尔滨市', 0);
INSERT INTO kt.districts VALUES (210000, '南京市', 0);
INSERT INTO kt.districts VALUES (310000, '杭州市', 0);
INSERT INTO kt.districts VALUES (230000, '合肥市', 0);
INSERT INTO kt.districts VALUES (350000, '福州市', 0);
INSERT INTO kt.districts VALUES (330000, '南昌市', 0);
INSERT INTO kt.districts VALUES (250000, '济南市', 0);
INSERT INTO kt.districts VALUES (450000, '郑州市', 0);
INSERT INTO kt.districts VALUES (430000, '武汉市', 0);
INSERT INTO kt.districts VALUES (410000, '长沙市', 0);
INSERT INTO kt.districts VALUES (510000, '广州市', 0);
INSERT INTO kt.districts VALUES (570000, '海口市', 0);
INSERT INTO kt.districts VALUES (610000, '成都市', 0);
INSERT INTO kt.districts VALUES (550000, '贵阳市', 0);
INSERT INTO kt.districts VALUES (650000, '昆明市', 0);
INSERT INTO kt.districts VALUES (850000, '拉萨市', 0);
INSERT INTO kt.districts VALUES (710000, '西安市', 0);
INSERT INTO kt.districts VALUES (730000, '兰州市', 0);
INSERT INTO kt.districts VALUES (810000, '西宁市', 0);
INSERT INTO kt.districts VALUES (750000, '银川市', 0);
INSERT INTO kt.districts VALUES (830000, '乌鲁木齐市', 0);

INSERT INTO kt.districts VALUES (518000, '深圳市', 0);
INSERT INTO kt.districts VALUES (519000, '珠海市', 0);
INSERT INTO kt.districts VALUES (515000, '汕头市', 0);
INSERT INTO kt.districts VALUES (361000, '厦门市', 0);
INSERT INTO kt.districts VALUES (572000, '三亚市', 0);

-- INSERT INTO kt.districts VALUES (100000, '北京市', 0);
INSERT INTO kt.districts VALUES (100010, '东城区', 100000);
INSERT INTO kt.districts VALUES (100032, '西城区', 100000);
INSERT INTO kt.districts VALUES (100071, '丰台区', 100000);
INSERT INTO kt.districts VALUES (100020, '朝阳区', 100000);
INSERT INTO kt.districts VALUES (100043, '石景山区', 100000);
INSERT INTO kt.districts VALUES (100089, '海淀区', 100000);
INSERT INTO kt.districts VALUES (102300, '门头沟区', 100000);
INSERT INTO kt.districts VALUES (102400, '房山区', 100000);
INSERT INTO kt.districts VALUES (101100, '通州区', 100000);
INSERT INTO kt.districts VALUES (101300, '顺义区', 100000);
INSERT INTO kt.districts VALUES (102200, '昌平区', 100000);
INSERT INTO kt.districts VALUES (102600, '大兴区', 100000);
INSERT INTO kt.districts VALUES (101400, '怀柔区', 100000);
INSERT INTO kt.districts VALUES (101200, '平谷区', 100000);
INSERT INTO kt.districts VALUES (101500, '密云区', 100000);
INSERT INTO kt.districts VALUES (102100, '延庆区', 100000);

-- INSERT INTO kt.districts VALUES (518000, '深圳市', 0);
INSERT INTO kt.districts VALUES (518001, '福田区', 518000);
INSERT INTO kt.districts VALUES (518002, '罗湖区', 518000);
INSERT INTO kt.districts VALUES (518003, '南山区', 518000);
INSERT INTO kt.districts VALUES (518004, '宝安区', 518000);
INSERT INTO kt.districts VALUES (518005, '龙岗区', 518000);
INSERT INTO kt.districts VALUES (518006, '坪山区', 518000);
INSERT INTO kt.districts VALUES (518007, '龙华区', 518000);
INSERT INTO kt.districts VALUES (518008, '盐田区', 518000);