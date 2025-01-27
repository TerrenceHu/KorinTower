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
	participants_count BIGINT,
	city VARCHAR(100) DEFAULT NULL,
	status INT DEFAULT 0,
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
	participants_count BIGINT,
	type INT DEFAULT 0,
	retries INT DEFAULT 0,
	status INT DEFAULT 0,
	updated_on DATE,
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
	city VARCHAR(100),
	district VARCHAR(100),
	age VARCHAR(100),
	price VARCHAR(100),
	height VARCHAR(100),
	weight VARCHAR(100),
	measurement VARCHAR(100),
	service VARCHAR(255),
	status INT DEFAULT 0,
	updated_on DATE
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
INSERT INTO kt.districts VALUES (100010, '东城', 100000);
INSERT INTO kt.districts VALUES (100032, '西城', 100000);
INSERT INTO kt.districts VALUES (100071, '丰台', 100000);
INSERT INTO kt.districts VALUES (100020, '朝阳', 100000);
INSERT INTO kt.districts VALUES (100043, '石景山', 100000);
INSERT INTO kt.districts VALUES (100089, '海淀', 100000);
INSERT INTO kt.districts VALUES (102300, '门头沟', 100000);
INSERT INTO kt.districts VALUES (102400, '房山', 100000);
INSERT INTO kt.districts VALUES (101100, '通州', 100000);
INSERT INTO kt.districts VALUES (101300, '顺义', 100000);
INSERT INTO kt.districts VALUES (102200, '昌平', 100000);
INSERT INTO kt.districts VALUES (102600, '大兴', 100000);
INSERT INTO kt.districts VALUES (101400, '怀柔', 100000);
INSERT INTO kt.districts VALUES (101200, '平谷', 100000);
INSERT INTO kt.districts VALUES (101500, '密云', 100000);
INSERT INTO kt.districts VALUES (102100, '延庆', 100000);

-- INSERT INTO kt.districts VALUES (200000, '上海市', 0);
INSERT INTO kt.districts VALUES (200001, '黄浦', 200000);
INSERT INTO kt.districts VALUES (200002, '徐汇', 200000);
INSERT INTO kt.districts VALUES (200003, '长宁', 200000);
INSERT INTO kt.districts VALUES (200004, '静安', 200000);
INSERT INTO kt.districts VALUES (200005, '普陀', 200000);
INSERT INTO kt.districts VALUES (200006, '虹口', 200000);
INSERT INTO kt.districts VALUES (200007, '杨浦', 200000);
INSERT INTO kt.districts VALUES (200008, '闵行', 200000);
INSERT INTO kt.districts VALUES (200009, '宝山', 200000);
INSERT INTO kt.districts VALUES (200010, '嘉定', 200000);
INSERT INTO kt.districts VALUES (200011, '浦东', 200000);
INSERT INTO kt.districts VALUES (200012, '金山', 200000);
INSERT INTO kt.districts VALUES (200013, '松江', 200000);
INSERT INTO kt.districts VALUES (200014, '青浦', 200000);
INSERT INTO kt.districts VALUES (200015, '奉贤', 200000);
INSERT INTO kt.districts VALUES (200016, '崇明', 200000);

-- INSERT INTO kt.districts VALUES (510000, '广州市', 0);
INSERT INTO kt.districts VALUES (510001, '越秀', 510000);
INSERT INTO kt.districts VALUES (510002, '荔湾', 510000);
INSERT INTO kt.districts VALUES (510003, '海珠', 510000);
INSERT INTO kt.districts VALUES (510004, '天河', 510000);
INSERT INTO kt.districts VALUES (510005, '白云', 510000);
INSERT INTO kt.districts VALUES (510006, '黄埔', 510000);
INSERT INTO kt.districts VALUES (510007, '番禺', 510000);
INSERT INTO kt.districts VALUES (510008, '花都', 510000);
INSERT INTO kt.districts VALUES (510009, '南沙', 510000);
INSERT INTO kt.districts VALUES (510010, '从化', 510000);
INSERT INTO kt.districts VALUES (510011, '增城', 510000);

-- INSERT INTO kt.districts VALUES (518000, '深圳市', 0);
INSERT INTO kt.districts VALUES (518001, '福田', 518000);
INSERT INTO kt.districts VALUES (518002, '罗湖', 518000);
INSERT INTO kt.districts VALUES (518003, '南山', 518000);
INSERT INTO kt.districts VALUES (518004, '宝安', 518000);
INSERT INTO kt.districts VALUES (518005, '龙岗', 518000);
INSERT INTO kt.districts VALUES (518006, '坪山', 518000);
INSERT INTO kt.districts VALUES (518007, '龙华', 518000);
INSERT INTO kt.districts VALUES (518008, '光明', 518000);
INSERT INTO kt.districts VALUES (518009, '盐田', 518000);
