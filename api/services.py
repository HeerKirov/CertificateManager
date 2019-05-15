from openpyxl import Workbook
from . import models as app_models, serializers as app_serializers
from CertificateManager.settings import TEMP_DIRS, IMAGE_DIRS
import os
import zipfile

EXCEL_RECORD_FIELD_NAME = {
    'id': '编号',
    'works_name': '作品名称',
    'award_level': '获奖等级',
    'competition_name': '竞赛名称',
    'competition_category': '竞赛类别',
    'hold_time': '举办时间',
    'organizer': '主办方',
    'rating_category': '竞赛评级分类',
    'rating_level_title': '竞赛评级等级',
    'main_student_location': '第一负责人所在班级',
    'main_student': '第一负责人',
    'other_students': '其他成员',
    'teacher': '指导教师'
}
EXCEL_RECORD_FIELD_COL = {
    'id': 'A',
    'competition_name': 'B',
    'competition_category': 'C',
    'hold_time': 'D',
    'organizer': 'E',
    'works_name': 'F',
    'award_level': 'G',
    'rating_category': 'H',
    'rating_level_title': 'I',
    'main_student_location': 'J',
    'main_student': 'K',
    'other_students': 'L',
    'teacher': 'M'
}
EXCEL_RECORD_FIELD_COL_WIDTH = {
    'id': 4,
    'competition_name': 20,
    'competition_category': 8,
    'hold_time': 10,
    'organizer': 12,
    'works_name': 12,
    'award_level': 8,
    'rating_category': 12,
    'rating_level_title': 12,
    'main_student_location': 40,
    'main_student': 10,
    'other_students': 20,
    'teacher': 10
}

IMAGE_CATEGORY_NAME = {
    'NOTICE': '比赛通知',
    'AWARD': '获奖证书',
    'LIST': '获奖名单页'
}


class Batch:
    @staticmethod
    def batch_class(data):
        colleges = {}
        subjects = {}
        result = []
        for d in data:
            serializer = app_serializers.Admin.ClassBatch(data=d)
            serializer.is_valid(raise_exception=True)

            grade = serializer.validated_data['grade']
            number = serializer.validated_data['number']
            subject = serializer.validated_data['subject']
            college = serializer.validated_data.get('college', None)

            if college in colleges:
                college_obj = colleges[college]
            else:
                college_obj = app_models.College.objects.filter(name=college).first()
                if college_obj is None:
                    college_obj = app_models.College(name=college)
                    college_obj.save()
                colleges[college] = college_obj

            if subject in subjects:
                subject_obj = subjects[subject]
            else:
                subject_obj = app_models.Subject.objects.filter(name=subject).first()
                if subject_obj is None:
                    subject_obj = app_models.Subject(name=subject, college=college_obj)
                    subject_obj.save()
                # 批处理将不修改现有的subject的college所属
                subjects[subject] = subject_obj

            obj = app_models.Class.objects.filter(grade=grade, number=number, subject=subject_obj).first()
            if obj is None:
                obj = app_models.Class(grade=grade, number=number, subject=subject_obj)
                obj.save()
            elif subject_obj != obj.subject:
                obj.subject = subject_obj
                obj.save()
            result.append({'grade': grade, 'number': number, 'subject': subject, 'college': subject_obj.college.name})
        return result

    @staticmethod
    def batch_student(data):
        result = []
        for d in data:
            serializer = app_serializers.Admin.StudentBatch(data=d)
            serializer.is_valid(raise_exception=True)

            card_id = serializer.validated_data['card_id']
            name = serializer.validated_data['name']
            grade = serializer.validated_data['clazz_grade']
            number = serializer.validated_data['clazz_number']
            subject = serializer.validated_data['subject']
            college = serializer.validated_data.get('college', None)

            clazz_objects = Batch.batch_class([{'grade': grade, 'number': number, 'subject': subject, 'college': college}])
            if len(clazz_objects) > 0:
                clazz_obj = app_models.Class.objects.filter(grade=clazz_objects[0]['grade'],
                                                            number=clazz_objects[0]['number'],
                                                            subject__name=clazz_objects[0]['subject']).first()
            else:
                clazz_obj = None

            obj = app_models.Student.objects.filter(card_id=card_id).first()
            if obj is None:
                obj = app_models.Student(card_id=card_id, name=name, clazz=clazz_obj)
                obj.save()
            else:
                obj.name = name
                obj.clazz = clazz_obj
                obj.save()
            result.append({'card_id': card_id, 'name': name, 'grade': grade, 'number': number, 'subject': subject, 'college': obj.college_name})
        return result

    @staticmethod
    def batch_teacher(data):
        pass


class Download:
    @staticmethod
    def generate_excel(data, filepath):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = '竞赛记录表'
        for (field, col) in EXCEL_RECORD_FIELD_COL.items():
            sheet['%s1' % (col,)] = EXCEL_RECORD_FIELD_NAME[field]
            sheet.column_dimensions[col].width = EXCEL_RECORD_FIELD_COL_WIDTH[field]
        cnt = 1
        for record in data:
            cnt += 1
            if record['teacher'] is not None:
                record['teacher'] = record['teacher_info']['name']
            if record['main_student'] is not None:
                info = record['main_student_info']
                record['main_student_location'] = '%s %s%s级%s班' % (info['college'], info['subject'], info['clazz_grade'], info['clazz_number'])
                record['main_student'] = info['name']
            if record['students'] is not None:
                record['other_students'] = ', '.join(student['name'] for student in record['students_info'])
            for (field, col) in EXCEL_RECORD_FIELD_COL.items():
                sheet['%s%s' % (col, cnt)] = record.get(field, None)
        workbook.save(filepath)

    @staticmethod
    def generate_zip(data, uid):
        if not os.path.exists(TEMP_DIRS):
            os.mkdir(TEMP_DIRS)
        Download.generate_excel(data, '%s/%s.xlsx' % (TEMP_DIRS, uid))
        image_list = []
        for item in data:
            for image in item['images']:
                if 'file' in image and 'category' in image:
                    image_list.append((
                        '%s/%s' % (IMAGE_DIRS, image['file']),
                        '%s-%s%s' % (item['id'], IMAGE_CATEGORY_NAME[image['category']], Download.get_ext(image['file']))
                    ))
        with zipfile.ZipFile('%s/%s.zip' % (TEMP_DIRS, uid), 'w') as package:
            package.write('%s/%s.xlsx' % (TEMP_DIRS, uid), arcname='报表.xlsx')
            for (filepath, filename) in image_list:
                package.write(filepath, arcname=filename)
        os.remove('%s/%s.xlsx' % (TEMP_DIRS, uid))
        return '%s/%s.zip' % (TEMP_DIRS, uid)

    @staticmethod
    def get_ext(filename):
        location = filename.rindex('.')
        if location >= 0:
            return filename[location:]
        return ''
