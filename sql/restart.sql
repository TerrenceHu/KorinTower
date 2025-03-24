TRUNCATE TABLE kt.channels;
TRUNCATE TABLE kt.channel_messages;
TRUNCATE TABLE kt.user_channels;
TRUNCATE TABLE kt.users;


SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE kt.teachers_info;
TRUNCATE TABLE kt.reports;
TRUNCATE TABLE kt.teachers;
SET FOREIGN_KEY_CHECKS = 1;