from django.shortcuts import render
from django.http import HttpResponse, FileResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib.auth import authenticate, login, logout
from rest_framework import viewsets, response, status, exceptions, permissions, mixins
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from . import exceptions as app_exceptions, serializers as app_serializers, models as app_models, permissions as app_permissions, services
from . import enums, filters as app_filters
from CertificateManager.settings import IMAGE_DIRS
import os
import uuid


class Auth:
    class Login(viewsets.ViewSet):
        @staticmethod
        def create(request):
            if request.user.is_authenticated:
                raise app_exceptions.AlreadyLogin()
            data = request.data
            app_serializers.Auth.Login(data=data).is_valid(raise_exception=True)
            user_type = data['user_type']
            username = data['username']
            password = data['password']
            user = authenticate(username='%s:%s' % (user_type, username), password=password)
            if user is not None:
                login(request, user)
                user.last_login = timezone.now()
                user.save()
                return response.Response(status=status.HTTP_200_OK)
            else:
                raise exceptions.AuthenticationFailed()

    class Logout(viewsets.ViewSet):
        permission_classes = (permissions.IsAuthenticated,)

        @staticmethod
        def create(request):
            logout(request)
            return response.Response(status=status.HTTP_200_OK)

    class Token(viewsets.ViewSet):
        @staticmethod
        def create(request):
            if request.user.is_authenticated:
                raise app_exceptions.AlreadyLogin()
            data = request.data
            app_serializers.Auth.Login(data=data).is_valid(raise_exception=True)
            user_type = data['user_type']
            username = data['username']
            password = data['password']
            user = authenticate(username='%s:%s' % (user_type, username), password=password)
            if user is not None:
                token, created = Token.objects.get_or_create(user=user)
                user.last_login = timezone.now()
                user.save()
                return response.Response({'token': token.key}, status=status.HTTP_200_OK)
            raise exceptions.AuthenticationFailed()

    class Info(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
        queryset = app_models.User.objects.all()
        serializer_class = app_serializers.Auth.Info
        permission_classes = (app_permissions.IsLogin,)
        lookup_field = 'username'

        def list(self, request, *args, **kwargs):
            profile = request.user
            self.kwargs['username'] = profile.username
            return self.retrieve(request, *args, **kwargs)


class Student:
    class Record(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                 viewsets.GenericViewSet):
        queryset = app_models.AwardRecord.objects
        serializer_class = app_serializers.Student.Record
        permission_classes = (app_permissions.IsStudent,)
        lookup_field = 'id'
        filterset_class = app_filters.Record
        ordering = '-update_time'

        def get_queryset(self):
            user = self.request.user
            return self.queryset.filter(submit_user=user).all()

        def perform_create(self, serializer):
            serializer.validated_data['submit_user'] = self.request.user
            super().perform_create(serializer)

        def destroy(self, request, *args, **kwargs):
            instance = self.get_object()
            if hasattr(instance, 'review') and getattr(instance, 'review').status == enums.ReviewStatus.waiting:
                instance.delete()
                return response.Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return response.Response(status=status.HTTP_403_FORBIDDEN)

    class Image(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
        queryset = app_models.Image.objects
        serializer_class = app_serializers.Student.Image
        permission_classes = (app_permissions.IsStudent,)
        lookup_field = 'id'
        filter_fields = ('id', 'category', 'award_record__id')

        def get_queryset(self):
            user = self.request.user
            return self.queryset.filter(award_record__submit_user=user).all()

        def create(self, request):
            award_record = request.POST.get('award_record')
            category = request.POST.get('category')
            file = request.FILES.get('file')
            if not app_models.AwardRecord.objects.filter(id=award_record).exists():
                return response.Response(status=404)
            if category != enums.ImageCategory.notice and category != enums.ImageCategory.award and \
                    category != enums.ImageCategory.list:
                return response.Response(status=400)
            name, ext = self.split_filename(file.name)
            image = app_models.Image.objects.filter(award_record_id=award_record, category=category).first()
            if image is None:
                image = app_models.Image(award_record_id=award_record, category=category, file=None)
            # 删除旧的文件
            if image.file is not None:
                old_path = '%s/%s' % (IMAGE_DIRS, image.file)
                if os.path.exists(old_path):
                    os.remove(old_path)
                image.file = None
            # 计算新文件名和新文件路径
            new_image_name = '%s-%s-%s.%s' % (award_record, category, uuid.uuid4(), ext)
            new_path = '%s/%s' % (IMAGE_DIRS, new_image_name)
            # 将文件名保存下来
            image.file = new_image_name
            image.save()
            # 存储路径不存在时先创建路径
            if not os.path.exists(IMAGE_DIRS):
                os.makedirs(IMAGE_DIRS)
            # 该文件万一已经存在，就删除文件
            if os.path.exists(new_path):
                os.remove(new_path)
            with open(new_path, 'wb') as f:
                for c in file.chunks():
                    f.write(c)
            return response.Response({'award_record': award_record, 'category': category, 'file': new_image_name}, status=201)

        @staticmethod
        def split_filename(filename):
            p = filename.rfind('.')
            if p >= 0:
                return filename[:p], filename[p + 1:]
            else:
                return filename, ''

    class Class(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
        queryset = app_models.Class.objects
        serializer_class = app_serializers.Student.Class
        permission_classes = (app_permissions.IsStudent,)
        lookup_field = 'id'
        filter_fields = ('grade', 'number', 'subject__name', 'subject__college__name')
        search_fields = ('subject__name', 'grade', 'number')
        ordering_fields = ('grade', 'number', 'subject__name', 'subject__college__name')

    class Student(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
        queryset = app_models.Student.objects
        serializer_class = app_serializers.Student.Student
        permission_classes = (app_permissions.IsStudent,)
        lookup_field = 'card_id'
        filter_fields = ('card_id', 'name', 'clazz__grade', 'clazz__number', 'clazz__subject__name', 'clazz__subject__college__name')
        search_fields = ('card_id', 'name', 'clazz__subject__name', 'clazz__subject__college__name')
        ordering_fields = ('card_id', 'clazz__grade', 'clazz__number', 'clazz__subject__name', 'clazz__subject__college__name')

    class Teacher(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
        queryset = app_models.Teacher.objects
        serializer_class = app_serializers.Student.Teacher
        permission_classes = (app_permissions.IsStudent,)
        lookup_field = 'card_id'
        filter_fields = ('card_id', 'name')
        search_fields = ('card_id', 'name')
        ordering_fields = ('card_id',)


class Admin:
    class CollegeBatch(viewsets.ViewSet):
        @staticmethod
        def create(request):
            data = request.data
            result = []
            for d in data:
                serializer = app_serializers.Admin.College(data=d)
                serializer.is_valid(raise_exception=True)
                name = serializer.validated_data['name']
                obj = app_models.College.objects.filter(name=name).first()
                if obj is None:
                    serializer.save()
                    result.append(serializer.validated_data)
                else:
                    serializer.instance = obj
                    result.append(serializer.validated_data)
            return response.Response(result, status=status.HTTP_201_CREATED)

    class SubjectBatch(viewsets.ViewSet):
        @staticmethod
        def create(request):
            data = request.data
            result = []
            for d in data:
                serializer = app_serializers.Admin.SubjectBatch(data=d)
                serializer.is_valid(raise_exception=True)

                name = serializer.validated_data['name']
                college = serializer.validated_data['college']

                college_obj = app_models.College.objects.filter(name=college).first()
                if college_obj is None:
                    college_obj = app_models.College(name=college)
                    college_obj.save()
                obj = app_models.Subject.objects.filter(name=name).first()
                if obj is None:
                    obj = app_models.Subject(name=name, college=college_obj)
                    obj.save()
                elif college_obj != obj.college:
                    obj.college = college_obj
                    obj.save()
                result.append({'name': name, 'college': college})
            return response.Response(result, status=status.HTTP_201_CREATED)

    class ClassBatch(viewsets.ViewSet):
        @staticmethod
        def create(request):
            data = request.data
            result = services.Batch.batch_class(data)
            return response.Response(result, status=status.HTTP_201_CREATED)

    class College(viewsets.ModelViewSet):
        queryset = app_models.College.objects
        serializer_class = app_serializers.Admin.College
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'name'
        filter_fields = ('name',)
        search_fields = ('name',)

    class Subject(viewsets.ModelViewSet):
        queryset = app_models.Subject.objects
        serializer_class = app_serializers.Admin.Subject
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'name'
        filter_fields = ('name', 'college__name')
        search_fields = ('name',)

    class Class(viewsets.ModelViewSet):
        queryset = app_models.Class.objects
        serializer_class = app_serializers.Admin.Class
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'id'
        filter_fields = ('grade', 'number', 'subject__name', 'subject__college__name')
        search_fields = ('subject__name', 'grade', 'number')
        ordering_fields = ('grade', 'number', 'subject__name', 'subject__college__name')

    class Student(viewsets.ModelViewSet):
        queryset = app_models.Student.objects
        serializer_class = app_serializers.Admin.Student
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'card_id'
        filter_fields = ('card_id', 'name', 'clazz__grade', 'clazz__number', 'clazz__subject__name', 'clazz__subject__college__name')
        search_fields = ('card_id', 'name', 'clazz__subject__name', 'clazz__subject__college__name')
        ordering_fields = ('card_id', 'clazz__grade', 'clazz__number', 'clazz__subject__name', 'clazz__subject__college__name')

    class Teacher(viewsets.ModelViewSet):
        queryset = app_models.Teacher.objects
        serializer_class = app_serializers.Admin.Teacher
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'card_id'
        filter_fields = ('card_id', 'name')
        search_fields = ('card_id', 'name')
        ordering_fields = ('card_id',)

    class StudentBatch(viewsets.ViewSet):
        @staticmethod
        def create(request):
            data = request.data
            result = services.Batch.batch_student(data)
            return response.Response(result, status=status.HTTP_201_CREATED)

    class TeacherBatch(viewsets.ViewSet):
        @staticmethod
        def create(request):
            data = request.data
            result = []
            for d in data:
                serializer = app_serializers.Admin.Teacher(data=d)
                serializer.is_valid(raise_exception=True)
                name = serializer.validated_data['name']
                card_id = serializer.validated_data['card_id']
                obj = app_models.Teacher.objects.filter(card_id=card_id).first()
                if obj is None:
                    serializer.save()
                    result.append(serializer.validated_data)
                else:
                    serializer.instance = obj
                    obj.name = name
                    obj.save()
                    result.append(serializer.validated_data)
            return response.Response(result, status=status.HTTP_201_CREATED)

    class RatingInfo(viewsets.ModelViewSet):
        queryset = app_models.RatingInfo.objects
        serializer_class = app_serializers.Admin.RatingInfo
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'id'
        filter_fields = ('level_title', 'level', 'category')
        search_fields = ('category', 'competition_name')
        ordering_fields = ('level', 'category')

    class RatingInfoBatch(viewsets.ViewSet):
        @staticmethod
        def create(request):
            data = request.data
            result = []
            for d in data:
                serializer = app_serializers.Admin.RatingInfo(data=d)
                serializer.is_valid(raise_exception=True)
                competition_name = serializer.validated_data['competition_name']
                category = serializer.validated_data['category']
                level_title = serializer.validated_data['level_title']
                level = serializer.validated_data['level']
                obj = app_models.RatingInfo.objects.filter(competition_name=competition_name).first()
                if obj is None:
                    serializer.save()
                    result.append(serializer.validated_data)
                else:
                    serializer.instance = obj
                    obj.category = category
                    obj.level_title = level_title
                    obj.level = level
                    obj.save()
                    result.append(serializer.validated_data)
            return response.Response(result, status=status.HTTP_201_CREATED)

    class Competition(viewsets.ModelViewSet):
        queryset = app_models.Competition.objects
        serializer_class = app_serializers.Admin.Competition
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'name'
        filter_fields = ('name', 'rating_info', 'category')
        ordering_fields = ('rating_info', 'category', 'hold_time')
        search_fields = ('name', 'organizer', 'category')

    class User(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
        queryset = app_models.User.objects
        serializer_class = app_serializers.Admin.User
        permission_classes = (app_permissions.IsStaff,)
        filterset_class = app_filters.User
        search_fields = ('username', 'first_name')

        def perform_create(self, serializer):
            user_type = serializer.validated_data.get('user_type')
            username = serializer.validated_data.get('username')
            password = serializer.validated_data.get('password', None) or username
            name = serializer.validated_data.get('name', None)
            if user_type == enums.UserType.admin:
                if name is None:
                    name = username
                user = app_models.User(username='%s:%s' % (user_type, username), first_name=name, is_staff=True)
                user.set_password(password)
                user.save()
            elif user_type == enums.UserType.student:
                student = app_models.Student.objects.filter(card_id=username).first()
                if student is None:
                    raise app_exceptions.ApiError('StudentNotExist', 'Student %s is not exist.' % (username,))
                if student.user is not None:
                    raise app_exceptions.ApiError('StudentExist', 'Student %s already has user id.' % (username,))
                if name is None:
                    name = student.name
                user = app_models.User(username='%s:%s' % (user_type, username), first_name=name)
                user.set_password(password)
                user.save()
                student.user = user
                student.save()
            elif user_type == enums.UserType.teacher:
                teacher = app_models.Teacher.objects.filter(card_id=username).first()
                if teacher is None:
                    raise app_exceptions.ApiError('TeacherNotExist', 'Teacher %s is not exist.' % (username,))
                if teacher.user is not None:
                    raise app_exceptions.ApiError('TeacherExist', 'Teacher %s already has user id.' % (username,))
                if name is None:
                    name = teacher.name
                user = app_models.User(username='%s:%s' % (user_type, username), first_name=name)
                user.set_password(password)
                user.save()
                teacher.user = user
                teacher.save()

    class UserDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
        queryset = app_models.User.objects
        serializer_class = app_serializers.Admin.UserDetail
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'username'

        def perform_update(self, serializer):
            password = serializer.validated_data.pop('password', None)
            if password is not None:
                user = serializer.instance
                user.set_password(password)
                user.save()
            super().perform_update(serializer)

    class Record(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
        queryset = app_models.AwardRecord.objects
        serializer_class = app_serializers.Admin.Record
        permission_classes = (app_permissions.IsStaff,)
        lookup_field = 'id'
        filterset_class = app_filters.Record
        ordering = '-update_time'
        search_fields = ('works_name', 'award_level', 'competition_record__name', 'teacher__name', 'students__name', 'main_student__name')

        @action(methods=['GET'], detail=False)
        def download(self, request):
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            file = services.Download.generate_zip(serializer.data, uuid.uuid4())
            res = FileResponse(open(file, 'rb'), as_attachment=True, filename='打包.zip')
            os.remove(file)
            return res
