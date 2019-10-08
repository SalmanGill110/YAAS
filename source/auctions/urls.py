from django.conf.urls import url
from . import views

app_name = 'auctions'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^myauctions/$', views.my_auctions, name='myauctions'),
    url(r'^browse/$', views.browse, name='browse'),
    url(r'^banned/$', views.browse_banned, name='banned'),
    url(r'^(?P<auction_id>[0-9]+)/$', views.detail, name='detail'),
    url(r'^auction/add/$', views.create_auction, name='auction-add'),
    url(r'^auction/confirm/$', views.confirm_auction, name='auction-confirm'),
    url(r'^auction/(?P<pk>[0-9]+)/edit/$', views.AuctionEditFormView.as_view(), name='auction-update'),
    url(r'^language/$', views.change_language, name='language'),
    url(r'^auction/(?P<pk>[0-9]+)/ban/$', views.auction_ban, name='auction-ban'),
    url(r'^auction/(?P<pk>[0-9]+)/unban/$', views.auction_unban, name='auction-unban'),
    url(r'^auction/(?P<auction_id>[0-9]+)/bid/$', views.BidFormFormView.as_view() , name='bid'),
    url(r'^auction/non/edit/(?P<edit_token>[\w\-]+)/$', views.AuctionEditFormNonView.as_view(), name='auction-edit-without'),
]