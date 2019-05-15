import django_filters
from . import models as app_models


class Record(django_filters.FilterSet):
    review__status = django_filters.CharFilter(field_name='review__status', lookup_expr='iexact')
    update_time__gte = django_filters.DateTimeFilter(field_name='update_time', lookup_expr='gte')
    update_time__lte = django_filters.DateTimeFilter(field_name='update_time', lookup_expr='lte')

    class Meta:
        model = app_models.AwardRecord
        fields = ('update_time__gte', 'update_time__lte', 'review__status')


class User(django_filters.FilterSet):
    is_staff = django_filters.BooleanFilter(field_name='is_staff', lookup_expr='exact')
    user_type = django_filters.CharFilter(field_name='username', lookup_expr='startswith')

    class Meta:
        model = app_models.User
        fields = ('is_staff', 'user_type')
