from django.conf.urls import url
from django.conf.urls import include, url
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
import django.contrib.auth.views as django_views

from . import views

urlpatterns = [
	#index
	url(r'^$', views.index, name='index'),
	url(r'^([0-9]{4})/$', views.index, name='index'),

	# /login
	url(r'^login/$', django_views.login, {'template_name': 'login.html'}, name='login'),
	#url(r'^login/$', views.login, name='login'),
	url(r'^logout/$', django_views.logout, {'next_page': '/login'}, name='logout'),

	# /users
	url(r'users$', views.users, name='users'),
	url(r'users/([0-9]{4})/$', views.users, name='users'),

	# /projects
	url(r'projects$', views.projects, name='projects'),
	url(r'projects/([0-9]{4})/$', views.projects, name='projects'),

	url(r'^export/xls/([0-9]{4})/$', views.export_xls, name='export_xls'),
]
