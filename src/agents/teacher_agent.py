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

    def get_reports_of_teachers(self, teachers):
        reports_of_teachers = {}
        for teacher in teachers:
            teacher_id = teacher[0]
            reports_of_teachers[teacher_id] = self.get_reports_by_teacher_id(teacher_id)
        return reports_of_teachers

    def get_reports_by_teacher_id(self, teacher_id):
        reports = self.teacher_model.get_reports_by_teacher_id(teacher_id)
        return reports