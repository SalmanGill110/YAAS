from auctions.models import *
from django.contrib.auth.models import User
import random
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from auctions.views import get_random_string
from django.db import transaction
from django.conf import settings


class DBPopulator:
    # Add user to database
    def addUser(self, num):
        user = User()
        user.username = 'user' + str(num)
        user.email = 'user' + str(num) + '@yaas.com'
        password = 'pass' + str(num)
        user.set_password(password)
        user.save()
        profile = Profile()
        profile.language = 'en'
        profile.user = user
        profile.save()

    # Add auction to database
    def addAuction(self, num):
        auction = Auction()
        auction.title = "title " + str(num)
        auction.description = "description of item " + str(num)
        # auction.duration_hours = random.randint(72, 200)
        auction.duration_hours = int(72)
        auction.starting_price = Decimal(0.05)
        auction.seller = User.objects.get(username="user" + str(num))
        auction.start_date = timezone.now()
        auction.end_date = auction.start_date + timedelta(hours=auction.duration_hours)
        auction.edit_token = auction.start_date.strftime('%Y%m%d%H%M%S') + get_random_string()
        auction.revision = 1
        auction.save()

    # Add bid to database
    def addBid(self, num):
        bid = Bid()
        auction = Auction.objects.get(title="title " + str(51 - num))
        bid.bid_amount = Decimal(0.06)
        bid.auction = auction
        bid.bidder = User.objects.get(username="user" + str(num + 1))
        bid.save()
        auction.winner_id = User.objects.get(username="user" + str(num + 1)).id
        auction.bid_price = bid.bid_amount
        auction.save()

    # Call above functions
    def populate(self):

        for num in range(1, 51):
            self.addUser(num)
        for num in range(1, 51):
            self.addAuction(num)
        for num in range(1, 11):
            self.addBid(num)
