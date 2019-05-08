from django.db import models
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from . import enums

# Create your models here.


class College(models.Model):
    name = models.CharField(max_length=64, null=False, unique=True)

    def __str__(self):
        return '<%s>' % (self.name,)


class Subject(models.Model):
    name = models.CharField(max_length=64, null=False, unique=True)
    college = models.ForeignKey(College, related_name='subjects', on_delete=models.CASCADE)

    def __str__(self):
        return '<(%s)%s>' % (self.college.name, self.name)


class Class(models.Model):
    grade = models.IntegerField(null=False)
    number = models.IntegerField(null=False)
    subject = models.ForeignKey(Subject, related_name='classes', on_delete=models.CASCADE)

    @property
    def college_name(self):
        return self.subject.college.name

    def __str__(self):
        return '<(%s)%s %s级%s班>' % (self.subject.college.name, self.subject.name, self.grade, self.number)


class Student(models.Model):
    card_id = models.CharField(max_length=32, null=False, unique=True)
    name = models.CharField(max_length=16, null=False)
    clazz = models.ForeignKey(Class, related_name='students', null=True, on_delete=models.SET_NULL)
    user = models.OneToOneField(User, related_name='student', null=True, on_delete=models.SET_NULL)

    @property
    def clazz_grade(self):
        return self.clazz.grade

    @property
    def clazz_number(self):
        return self.clazz.number

    @property
    def subject_name(self):
        return self.clazz.subject.name

    @property
    def college_name(self):
        return self.clazz.subject.college.name

    def __str__(self):
        return '<%s %s>' % (self.card_id, self.name)


class Teacher(models.Model):
    card_id = models.CharField(max_length=32, null=False, unique=True)
    name = models.CharField(max_length=16, null=False)
    user = models.OneToOneField(User, related_name='teacher', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return '<%s %s>' % (self.card_id, self.name)


class AwardRecord(models.Model):
    works_name = models.CharField(max_length=128, null=True)
    award_level = models.CharField(max_length=16, null=False)
    update_time = models.DateTimeField(null=False)

    teacher = models.ForeignKey(Teacher, null=True, on_delete=models.SET_NULL)
    students = models.ManyToManyField(Student, related_name='award_records',
                                      through='AwardStudentRelation', through_fields=('award', 'student'))
    main_student = models.ForeignKey(Student, related_name='main_award_records', null=True, on_delete=models.SET_NULL)

    submit_user = models.ForeignKey(User, related_name='award_records', on_delete=models.SET_NULL, null=True)

    @property
    def competition_name(self):
        return self.competition_record.name

    @property
    def competition_category(self):
        return self.competition_record.category

    @property
    def hold_time(self):
        return self.competition_record.hold_time

    @property
    def organizer(self):
        return self.competition_record.organizer

    @property
    def review_status(self):
        return getattr(self, 'review').status if hasattr(self, 'review') else None

    @property
    def rating_category(self):
        rating = self.competition_record.competition.rating_info
        return rating.category if rating is not None else None

    @property
    def rating_level_title(self):
        rating = self.competition_record.competition.rating_info
        return rating.level_title if rating is not None else None

    @property
    def rating_level(self):
        rating = self.competition_record.competition.rating_info
        return rating.level if rating is not None else None

    @property
    def image_list(self):
        return self.images if hasattr(self, 'images') else Image.objects.none()

    def __str__(self):
        return '<%s>' % (self.competition_name,)


class Image(models.Model):
    category = models.CharField(max_length=32, null=False)
    file = models.CharField(max_length=256, null=False)
    award_record = models.ForeignKey(AwardRecord, on_delete=models.CASCADE, related_name='images')
    recognition = models.ForeignKey('Recognition', null=True, related_name='images', on_delete=models.SET_NULL)


class Recognition(models.Model):
    competition = models.ForeignKey('Competition', related_name='recognitions', on_delete=models.SET_NULL, null=True)

    version = models.CharField(max_length=32, null=True)
    category = models.CharField(max_length=32, null=False)

    field_model = JSONField(null=False)
    mapping_model = JSONField(null=False)


class CompetitionRecord(models.Model):
    name = models.CharField(max_length=128, null=False)         # 竞赛名称（实例名称，带届数）
    category = models.CharField(max_length=128, null=False)     # 竞赛类型
    hold_time = models.DateField(null=False)                    # 举办时间
    organizer = models.CharField(max_length=128, null=False)    # 组织者

    award_record = models.OneToOneField(AwardRecord, related_name='competition_record', on_delete=models.CASCADE)
    competition = models.ForeignKey('Competition', related_name='competition_records',
                                    on_delete=models.SET_NULL, null=True)


class Review(models.Model):
    status = models.CharField(choices=enums.REVIEW_STATUS, max_length=12, default=enums.ReviewStatus.waiting, null=False)
    award_record = models.OneToOneField(AwardRecord, related_name='review', on_delete=models.CASCADE)


class Competition(models.Model):
    name = models.CharField(max_length=128, null=False, primary_key=True)
    category = models.CharField(max_length=128, null=False)
    hold_time = models.DateField(null=False)
    organizer = models.CharField(max_length=128, null=False)
    rating_info = models.ForeignKey('RatingInfo', related_name='competitions', on_delete=models.SET_NULL, null=True)

    @property
    def rating_info_category(self):
        return self.rating_info.category if self.rating_info is not None else None

    @property
    def rating_info_level_title(self):
        return self.rating_info.level_title if self.rating_info is not None else None

    @property
    def rating_info_level(self):
        return self.rating_info.level if self.rating_info is not None else None


class RatingInfo(models.Model):
    competition_name = models.CharField(max_length=128, null=False, primary_key=True)
    category = models.CharField(max_length=16, null=False)
    level_title = models.CharField(max_length=16, null=False)
    level = models.IntegerField(null=False)

    def __str__(self):
        return '<%s (%s | %s)>' % (self.competition_name, self.category, self.level_title)


class AwardStudentRelation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    award = models.ForeignKey(AwardRecord, on_delete=models.CASCADE)
    is_principal = models.BooleanField(default=False)


class GlobalSetting(models.Model):
    upload_enable = models.BooleanField(null=False, default=True)
