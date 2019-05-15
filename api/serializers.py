from rest_framework import serializers, validators, exceptions
from django.utils import timezone
from . import models as app_models, enums


class Field:
    class Image(serializers.ModelSerializer):
        id = serializers.IntegerField(read_only=True)
        category = serializers.CharField(read_only=True)
        file = serializers.CharField(read_only=True)
        recognition = serializers.PrimaryKeyRelatedField(read_only=True)

        class Meta:
            model = app_models.Image
            fields = ('id', 'category', 'file', 'recognition')

    class Student(serializers.ModelSerializer):
        card_id = serializers.CharField(max_length=32, allow_null=False, allow_blank=False)
        name = serializers.CharField(max_length=16, allow_null=False, allow_blank=False)
        clazz_grade = serializers.IntegerField(read_only=True)
        clazz_number = serializers.IntegerField(read_only=True)
        subject = serializers.CharField(source='subject_name', read_only=True)
        college = serializers.CharField(source='college_name', read_only=True)

        class Meta:
            model = app_models.Student
            fields = ('card_id', 'name', 'clazz_grade', 'clazz_number', 'subject', 'college')

    class Teacher(serializers.ModelSerializer):
        card_id = serializers.CharField(max_length=32, allow_null=False, allow_blank=False)
        name = serializers.CharField(max_length=16, allow_null=False, allow_blank=False)

        class Meta:
            model = app_models.Teacher
            fields = ('card_id', 'name')


class Auth:
    class Login(serializers.Serializer):
        user_type = serializers.ChoiceField(enums.USER_TYPE)
        username = serializers.CharField(max_length=150, allow_null=False, allow_blank=False, write_only=True)
        password = serializers.CharField(max_length=256, allow_null=False, allow_blank=False, write_only=True)

        class Meta:
            fields = ('username', 'password', 'user_type')

    class Token(serializers.Serializer):
        user_type = serializers.ChoiceField(enums.USER_TYPE)
        username = serializers.CharField(max_length=150, allow_null=False, allow_blank=False, write_only=True)
        password = serializers.CharField(max_length=256, allow_null=False, allow_blank=False, write_only=True)

        class Meta:
            fields = ('username', 'password', 'user_type')

    class Info(serializers.ModelSerializer):
        id = serializers.IntegerField(read_only=True)
        username = serializers.CharField(read_only=True)
        name = serializers.CharField(max_length=32, allow_null=False, allow_blank=False, source='first_name')
        date_joined = serializers.DateTimeField(read_only=True)
        last_login = serializers.DateTimeField(read_only=True)

        is_staff = serializers.BooleanField(read_only=True)

        class Meta:
            model = app_models.User
            fields = ('id', 'username', 'name', 'last_login', 'date_joined', 'is_staff')


class Student:
    class Record(serializers.ModelSerializer):
        id = serializers.IntegerField(read_only=True)
        works_name = serializers.CharField(max_length=128, allow_null=True, allow_blank=True)
        award_level = serializers.CharField(max_length=32, allow_null=False)
        update_time = serializers.DateTimeField(read_only=True)
        teacher = serializers.SlugRelatedField(slug_field='card_id', queryset=app_models.Teacher.objects)
        students = serializers.SlugRelatedField(slug_field='card_id', many=True, queryset=app_models.Student.objects)
        main_student = serializers.SlugRelatedField(slug_field='card_id', queryset=app_models.Student.objects)

        teacher_info = Field.Teacher(source='teacher', read_only=True)
        students_info = Field.Student(source='students', many=True, read_only=True)
        main_student_info = Field.Student(source='main_student', read_only=True)

        competition_name = serializers.CharField(max_length=128, allow_null=False)
        competition_category = serializers.CharField(max_length=128, allow_null=False)
        hold_time = serializers.DateField(allow_null=False)
        organizer = serializers.CharField(max_length=128, allow_null=False)

        review_status = serializers.ChoiceField(choices=enums.REVIEW_STATUS, read_only=True)
        rating_category = serializers.CharField(max_length=16, allow_null=False, read_only=True)
        rating_level_title = serializers.CharField(max_length=16, allow_null=False, read_only=True)
        rating_level = serializers.IntegerField(allow_null=False, read_only=True)

        images = Field.Image(many=True, source='image_list', read_only=True)

        def create(self, validated_data):
            competition_name = validated_data.pop('competition_name')
            competition_category = validated_data.pop('competition_category')
            hold_time = validated_data.pop('hold_time')
            organizer = validated_data.pop('organizer')

            validated_data['update_time'] = timezone.now()
            record = super().create(validated_data)
            competition_record = app_models.CompetitionRecord(name=competition_name, category=competition_category,
                                                              hold_time=hold_time, organizer=organizer,
                                                              award_record=record)
            competition_record.save()
            review = app_models.Review(award_record=record)
            review.save()

            return record

        def update(self, instance, validated_data):
            competition_name = validated_data.pop('competition_name', None)
            competition_category = validated_data.pop('competition_category', None)
            hold_time = validated_data.pop('hold_time', None)
            organizer = validated_data.pop('organizer', None)

            validated_data['update_time'] = timezone.now()

            record = super().update(instance, validated_data)
            review = record.review
            review.status = enums.ReviewStatus.waiting
            review.save()
            if competition_name is not None or competition_category is not None or hold_time is not None or organizer is not None:
                competition_record = record.competition_record
                if competition_name is not None:
                    competition_record.name = competition_name
                if competition_category is not None:
                    competition_record.category = competition_category
                if hold_time is not None:
                    competition_record.hold_time = hold_time
                if organizer is not None:
                    competition_record.organizer = organizer
                competition_record.save()
            return record

        class Meta:
            model = app_models.AwardRecord
            fields = ('id', 'works_name', 'award_level', 'update_time', 'teacher', 'students', 'main_student',
                      'teacher_info', 'students_info', 'main_student_info',
                      'competition_name', 'competition_category', 'hold_time', 'organizer',
                      'review_status', 'rating_category', 'rating_level_title', 'rating_level', 'images')

    class Image(serializers.ModelSerializer):
        id = serializers.IntegerField(read_only=True)
        category = serializers.CharField(max_length=32, allow_null=False)
        file = serializers.CharField(max_length=256, allow_null=False)
        award_record = serializers.PrimaryKeyRelatedField(queryset=app_models.AwardRecord.objects)
        recognition = serializers.PrimaryKeyRelatedField(queryset=app_models.Recognition.objects)

        class Meta:
            model = app_models.Image
            fields = ('id', 'category', 'file', 'award_record', 'recognition')

    class Class(serializers.ModelSerializer):
        grade = serializers.IntegerField(read_only=True)
        number = serializers.IntegerField(read_only=True)
        subject = serializers.SlugRelatedField(slug_field='name', read_only=True)
        college = serializers.CharField(source='college_name')

        class Meta:
            model = app_models.Class
            fields = ('grade', 'number', 'subject', 'college')

    class Student(serializers.ModelSerializer):
        card_id = serializers.CharField(read_only=True)
        name = serializers.CharField(read_only=True)
        clazz = serializers.PrimaryKeyRelatedField(read_only=True)
        clazz_grade = serializers.IntegerField(read_only=True)
        clazz_number = serializers.IntegerField(read_only=True)
        subject = serializers.CharField(source='subject_name', read_only=True)
        college = serializers.CharField(source='college_name', read_only=True)

        class Meta:
            model = app_models.Student
            fields = ('card_id', 'name', 'clazz', 'clazz_grade', 'clazz_number', 'subject', 'college')

    class Teacher(serializers.ModelSerializer):
        card_id = serializers.CharField(read_only=True)
        name = serializers.CharField(read_only=True)

        class Meta:
            model = app_models.Teacher
            fields = ('card_id', 'name')


class Admin:
    class College(serializers.ModelSerializer):
        name = serializers.CharField(max_length=64, allow_null=False, allow_blank=False)

        class Meta:
            model = app_models.College
            fields = ('name',)

    class Subject(serializers.ModelSerializer):
        name = serializers.CharField(max_length=64, allow_null=False, allow_blank=False)
        college = serializers.SlugRelatedField(slug_field='name', queryset=app_models.College.objects)

        class Meta:
            model = app_models.Subject
            fields = ('name', 'college')

    class Class(serializers.ModelSerializer):
        grade = serializers.IntegerField(allow_null=False, min_value=1995)
        number = serializers.IntegerField(allow_null=False, min_value=1)
        subject = serializers.SlugRelatedField(slug_field='name', queryset=app_models.Subject.objects)
        college = serializers.CharField(source='college_name')

        class Meta:
            model = app_models.Class
            fields = ('grade', 'number', 'subject', 'college')

    class SubjectBatch(serializers.Serializer):
        name = serializers.CharField(max_length=64, allow_null=False, allow_blank=False)
        college = serializers.CharField(max_length=64, allow_null=False, allow_blank=False)

        class Meta:
            fields = ('name', 'college')

    class ClassBatch(serializers.Serializer):
        grade = serializers.IntegerField(allow_null=False, min_value=1995)
        number = serializers.IntegerField(allow_null=False, min_value=1)
        subject = serializers.CharField(max_length=64, allow_null=False, allow_blank=False)
        college = serializers.CharField(max_length=64, allow_null=False, allow_blank=False)

        class Meta:
            fields = ('grade', 'number', 'subject', 'college')

    class Student(serializers.ModelSerializer):
        card_id = serializers.CharField(max_length=32, allow_null=False, allow_blank=False)
        name = serializers.CharField(max_length=16, allow_null=False, allow_blank=False)
        clazz = serializers.PrimaryKeyRelatedField(queryset=app_models.Class.objects)
        clazz_grade = serializers.IntegerField(read_only=True)
        clazz_number = serializers.IntegerField(read_only=True)
        subject = serializers.CharField(source='subject_name', read_only=True)
        college = serializers.CharField(source='college_name', read_only=True)

        class Meta:
            model = app_models.Student
            fields = ('card_id', 'name', 'clazz', 'clazz_grade', 'clazz_number', 'subject', 'college')

    class Teacher(serializers.ModelSerializer):
        card_id = serializers.CharField(max_length=32, allow_null=False, allow_blank=False)
        name = serializers.CharField(max_length=16, allow_null=False, allow_blank=False)

        class Meta:
            model = app_models.Teacher
            fields = ('card_id', 'name')

    class StudentBatch(serializers.Serializer):
        card_id = serializers.CharField(max_length=32, allow_null=False, allow_blank=False)
        name = serializers.CharField(max_length=16, allow_null=False, allow_blank=False)
        clazz_grade = serializers.IntegerField(allow_null=False)
        clazz_number = serializers.IntegerField(allow_null=False)
        subject = serializers.CharField(max_length=64, allow_null=False, allow_blank=False)
        college = serializers.CharField(max_length=64, allow_null=False, allow_blank=False)

        class Meta:
            fields = ('card_id', 'name', 'clazz_grade', 'clazz_number', 'subject', 'college')

    class RatingInfo(serializers.ModelSerializer):
        competition_name = serializers.CharField(max_length=128, allow_null=False, allow_blank=False)
        category = serializers.CharField(max_length=16, allow_null=False)
        level_title = serializers.CharField(max_length=16, allow_null=False)
        level = serializers.IntegerField(allow_null=False)

        class Meta:
            model = app_models.RatingInfo
            fields = ('competition_name', 'category', 'level_title', 'level')

    class Competition(serializers.ModelSerializer):
        name = serializers.CharField(max_length=128, allow_null=False, allow_blank=False)
        category = serializers.CharField(max_length=128, allow_null=False)
        hold_time = serializers.DateField(allow_null=False)
        organizer = serializers.CharField(max_length=128, allow_null=False)
        rating_info = serializers.PrimaryKeyRelatedField(queryset=app_models.RatingInfo.objects, allow_null=True)
        rating_info_category = serializers.CharField(read_only=True)
        rating_info_level_title = serializers.CharField(read_only=True)
        rating_info_level = serializers.IntegerField(read_only=True)

        class Meta:
            model = app_models.Competition
            fields = ('name', 'category', 'hold_time', 'organizer', 'rating_info',
                      'rating_info_category', 'rating_info_level_title', 'rating_info_level')

    class User(serializers.Serializer):
        user_type = serializers.ChoiceField(enums.USER_TYPE, allow_null=False, write_only=True)
        username = serializers.CharField(max_length=32, allow_null=False)
        password = serializers.CharField(max_length=256, allow_null=True, allow_blank=False, required=False, write_only=True)
        name = serializers.CharField(max_length=30, allow_null=True, allow_blank=False, required=False, source='first_name')
        date_joined = serializers.DateTimeField(read_only=True)
        last_login = serializers.DateTimeField(read_only=True)

        class Meta:
            fields = ('user_type', 'username', 'password', 'name', 'date_joined', 'last_login')

    class UserDetail(serializers.ModelSerializer):
        username = serializers.CharField(read_only=True)
        password = serializers.CharField(max_length=256, allow_null=False, allow_blank=False, write_only=True, required=False)
        name = serializers.CharField(max_length=30, allow_null=False, allow_blank=False, source='first_name')
        date_joined = serializers.DateTimeField(read_only=True)
        last_login = serializers.DateTimeField(read_only=True)

        class Meta:
            model = app_models.User
            fields = ('username', 'password', 'name', 'date_joined', 'last_login')

    class Record(serializers.ModelSerializer):
        id = serializers.IntegerField(read_only=True)
        works_name = serializers.CharField(read_only=True)
        award_level = serializers.CharField(read_only=True)
        update_time = serializers.DateTimeField(read_only=True)
        teacher = serializers.SlugRelatedField(slug_field='card_id', read_only=True)
        students = serializers.SlugRelatedField(slug_field='card_id', many=True, read_only=True)
        main_student = serializers.SlugRelatedField(slug_field='card_id', read_only=True)

        teacher_info = Field.Teacher(source='teacher', read_only=True)
        students_info = Field.Student(source='students', many=True, read_only=True)
        main_student_info = Field.Student(source='main_student', read_only=True)

        competition_name = serializers.CharField(read_only=True)
        competition_category = serializers.CharField(read_only=True)
        hold_time = serializers.DateField(read_only=True)
        organizer = serializers.CharField(read_only=True)

        rating_category = serializers.CharField(max_length=16, allow_null=False, read_only=True)
        rating_level_title = serializers.CharField(max_length=16, allow_null=False, read_only=True)
        rating_level = serializers.IntegerField(allow_null=False, read_only=True)

        images = Field.Image(many=True, source='image_list', read_only=True)

        review_status = serializers.ChoiceField(choices=enums.REVIEW_STATUS)
        competition = serializers.PrimaryKeyRelatedField(queryset=app_models.Competition.objects,
                                                         allow_null=True, write_only=True)
        rating_info = serializers.PrimaryKeyRelatedField(queryset=app_models.RatingInfo.objects,
                                                         write_only=True, required=False, allow_null=True)

        def update(self, instance, validated_data):
            review_status = validated_data.pop('review_status')
            if hasattr(instance, 'review'):
                review = getattr(instance, 'review')
                if review is None:
                    review = app_models.Review(award_record=instance)
            else:
                review = app_models.Review(award_record=instance)
            review.status = review_status
            review.save()
            if review.status == enums.ReviewStatus.passed:
                competition_record = getattr(instance, 'competition_record')
                competition = validated_data.pop('competition')
                rating_info = validated_data.pop('rating_info', None)
                if competition is None and competition_record.competition is None:
                    if app_models.Competition.objects.filter(name=competition_record.name).exists():
                        competition = app_models.Competition.objects.filter(name=competition_record.name).first()
                    elif rating_info is None:
                        raise exceptions.ValidationError('rating_info is necessary.')
                    else:
                        competition = app_models.Competition(name=competition_record.name,
                                                             category=competition_record.category,
                                                             hold_time=competition_record.hold_time,
                                                             organizer=competition_record.organizer,
                                                             rating_info=rating_info)
                        competition.save()
                competition_record.competition = competition
                competition_record.name = competition.name
                competition_record.category = competition.category
                competition_record.organizer = competition.organizer
                competition_record.hold_time = competition.hold_time
                competition_record.save()
            return super().update(instance, validated_data)

        class Meta:
            model = app_models.AwardRecord
            fields = ('id', 'works_name', 'award_level', 'update_time', 'teacher', 'students', 'main_student',
                      'students_info', 'main_student_info', 'teacher_info',
                      'competition_name', 'competition_category', 'hold_time', 'organizer',
                      'review_status', 'rating_category', 'rating_level_title', 'rating_level', 'images',
                      'competition', 'rating_info')
