from django.conf.urls import url

from . import views

app_name = 'floybd'


urlpatterns = [
    url(r'^$', views.index, name='index'),
    url('getConcreteDateValues', views.getConcreteKML, name='getConcreteDateValues'),
]