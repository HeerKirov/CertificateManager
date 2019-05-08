from . import models as app_models, serializers as app_serializers


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
