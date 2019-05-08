from rest_framework import routers
from . import views as app_views

router = routers.DefaultRouter()

router.register('auth/login', app_views.Auth.Login, base_name='api-user-login')
router.register('auth/logout', app_views.Auth.Logout, base_name='api-user-logout')
router.register('auth/token', app_views.Auth.Token, base_name='api-user-token')
router.register('auth/info', app_views.Auth.Info, base_name='api-user-info')

router.register('student/records', app_views.Student.Record, base_name='api-student-record')
router.register('student/images', app_views.Student.Image, base_name='api-student-image')

router.register('admin/users', app_views.Admin.User, base_name='api-admin-user-list')
router.register('admin/users', app_views.Admin.UserDetail, base_name='api-admin-user-detail')

router.register('admin/colleges', app_views.Admin.College, base_name='api-admin-college')
router.register('admin/subjects', app_views.Admin.Subject, base_name='api-admin-subject')
router.register('admin/classes', app_views.Admin.Class, base_name='api-admin-class')
router.register('admin/college-batch', app_views.Admin.CollegeBatch, base_name='api-admin-college-batch')
router.register('admin/subject-batch', app_views.Admin.SubjectBatch, base_name='api-admin-subject-batch')
router.register('admin/class-batch', app_views.Admin.ClassBatch, base_name='api-admin-class-batch')
router.register('admin/students', app_views.Admin.Student, base_name='api-admin-student')
router.register('admin/teachers', app_views.Admin.Teacher, base_name='api-admin-teacher')
router.register('admin/student-batch', app_views.Admin.StudentBatch, base_name='api-admin-student-batch')
router.register('admin/teacher-batch', app_views.Admin.TeacherBatch, base_name='api-admin-teacher-batch')

router.register('admin/rating-info', app_views.Admin.RatingInfo, base_name='api-admin-rating-info')
router.register('admin/rating-info-batch', app_views.Admin.RatingInfoBatch, base_name='api-admin-rating-info-batch')
router.register('admin/competitions', app_views.Admin.Competition, base_name='api-admin-competition')
router.register('admin/records', app_views.Admin.Record, base_name='api-admin-record')

urlpatterns = []
urlpatterns += router.urls
