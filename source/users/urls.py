from django.conf.urls import url
from . import views

app_name = 'users'

urlpatterns = [
    url(r'^register/$', views.UserFormView.as_view(), name='register'),
    url(r'^editprofile/$', views.UserEditFormView.as_view(), name='editprofile'),
    url(r'^login/$', views.LoginFormView.as_view(), name='login'),
    url(r'^logout/$', views.logout_user, name='logout'),
]
