USER_TYPE = (
    ('ADMIN', 'Admin'),
    ('TEACHER', 'Teacher'),
    ('STUDENT', 'Student')
)


IMAGE_CATEGORY = (
    ('NOTICE', 'Notice'),
    ('AWARD', 'Award'),
    ('LIST', 'List')
)

REVIEW_STATUS = (
    ('WAITING', 'Waiting'),
    ('PASSED', 'Passed'),
    ('NOT_PASS', 'NotPass')
)


class UserType:
    admin = 'ADMIN'
    teacher = 'TEACHER'
    student = 'STUDENT'


class ImageCategory:
    notice = 'NOTICE'
    award = 'AWARD'
    list = 'LIST'


class ReviewStatus:
    waiting = 'WAITING'
    passed = 'PASSED'
    not_pass = 'NOT_PASS'
