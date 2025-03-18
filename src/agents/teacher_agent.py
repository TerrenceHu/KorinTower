from datetime import date, datetime
from configparser import ConfigParser
from loguru import logger

from globals import *
from utils.chat_utils import *

from models.teacher_model import TeacherModel

class TeacherAgent():
    def __init__(self, config: ConfigParser) -> None:
        # 群组、频道和用户的数据库模型
        self.db_host = config.get('DATABASE', 'db_host')
        self.db_user = config.get('DATABASE', 'db_user')
        self.db_password = config.get('DATABASE', 'db_password')
        self.db_database = config.get('DATABASE', 'db_database')
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



        
