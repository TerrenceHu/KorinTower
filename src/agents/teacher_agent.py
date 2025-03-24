from math import log10
from datetime import datetime
from configparser import ConfigParser
from loguru import logger

from globals import *
from utils.chat_utils import *

from models.channel_model import ChannelModel
from models.user_model import UserModel
from models.teacher_model import TeacherModel

class TeacherAgent():
    def __init__(self, config: ConfigParser) -> None:
        # 群组、频道和用户的数据库模型
        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
        self.channel_model = ChannelModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        self.user_model = UserModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
        self.teacher_model = TeacherModel(host=self.db_host, user=self.db_user,
                                          password=self.db_password, database=self.db_database)
    
    def get_teachers_by_city(self, city_id):
        teachers = self.teacher_model.get_effective_teachers_by_city(city_id)
        return teachers
    
    def get_teachers_by_district(self, district_id):
        teachers = self.teacher_model.get_effective_teachers_by_district(district_id)
        return teachers

    def get_reports_by_teacher_id(self, teacher_ids):
        if not teacher_ids:
            logger.warning("No teacher IDs provided for report retrieval")
            return {}
        
        reports = self.teacher_model.get_reports_by_teacher_id(teacher_ids)

        reports_dict = {teacher_id: [] for teacher_id in teacher_ids}
        for report in reports:
            teacher_id = report[0]
            reports_dict[teacher_id].append(report)
        
        return reports_dict


    def calc_score_of_teacher(self, teacher_id):
        count, comments, replies, reactions, views = 0, 0, 0, 0, 0
        latest_date = None

        channel_ids = self.user_model.get_channels_of_user(teacher_id)
        for channel_id in channel_ids:
            channel_messages = self.channel_model.get_channel_messages(channel_id)
            for message in channel_messages:
                count += 1
                comments += int(message[4])
                replies += message[5]
                reactions += message[6]
                views += message[7]
                if latest_date is None or message[8] > latest_date:
                    latest_date = message[8]
        
        if count > 0:
            comments = comments / count
            replies = replies / count
            reactions = reactions / count
            views = views / count
        
        if latest_date is not None:
            today_date = datetime.today()
            # 计算时间差，单位为周
            date_diff = (today_date - latest_date).days // 7
        else:
            date_diff = 100

        score = 1.0 * norm(comments) \
                + 1.0 * norm(replies) \
                + 1.0 * norm(reactions) \
                + 1.0 * norm(log10(views)) \
                + 1.0 * (1 - min(date_diff / 8, 1) ** 2)
        
        return score
