from django.conf.urls import url
from . import views
from django.views.decorators.csrf import csrf_exempt

app_name = 'api'

urlpatterns = [
    url(r'^auctions/$', views.AuctionsList.as_view()),
    url(r'^auctions/(?P<auction_id>[0-9]+)/$', views.AuctionDetails.as_view()),
    url(r'^auctions/(?P<auction_id>[0-9]+)/bid/$', csrf_exempt(views.BidOnAuction.as_view())),
]
