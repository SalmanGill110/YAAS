from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test.client import Client
from decimal import Decimal
from YAAS.views import populate_test_db

from auctions.models import *


class AuctionTest(TestCase):

    # Setup for tests
    def setUp(self):
        populate_test_db()
        self.user = User()
        self.user.username = 'testuser'
        self.user.email = 'testuser@testuser.com'
        self.user.set_password('testuser')
        self.user.save()
        self.profile = Profile()
        self.profile.user = self.user
        self.profile.language = 'en'
        self.profile.save()

    # Test to check user is not able to create auction without authentication
    def testCreateAuctionWithoutAuthentication(self):
        resp = self.client.post(reverse('auctions:auction-add'),
                                {'title': 'TestAuction', 'description': 'Auction Description',
                                 'duration_hours': int(77),
                                 'starting_price': 0.02})
        self.assertEqual(resp.status_code, 302)

    # Test to check that auction can be created with authenticated user (provided that all validation are passed)
    def testCreateAuctionWithAuthentication(self):
        # Login
        self.client.login(username='testuser', password='testuser')
        prevcount = Auction.objects.count()

        # Test bid duration 72 hours
        resp = self.client.post(reverse('auctions:auction-add'),
                                {'title': 'TestAuction', 'description': 'Auction Description',
                                 'duration_hours': int(71),
                                 'starting_price': 0.02})

        self.assertEqual(prevcount, Auction.objects.count())

        # Create auction with authentication
        resp = self.client.post(reverse('auctions:auction-add'),
                                {'title': 'TestAuction', 'description': 'Auction Description',
                                 'duration_hours': int(77),
                                 'starting_price': 0.02})

        self.failUnlessEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "auctions/auction_confirmation_form.html")

        # Test confirm = False
        resp = self.client.post(reverse('auctions:auction-confirm'),
                                {'confirm': 'False'})
        self.failUnlessEqual(resp.status_code, 302)
        self.assertEqual(prevcount, Auction.objects.count())

        # Test confirm = True
        resp = self.client.post(reverse('auctions:auction-confirm'),
                                {'confirm': 'True'})
        self.assertEqual(prevcount + 1, Auction.objects.count())
        latestAuction = Auction.objects.latest('start_date')
        self.assertEqual(latestAuction.title, 'TestAuction')


class BidTest(TestCase):

    # Setup for tests
    def setUp(self):
        # Populate data for tests
        populate_test_db()

        self.user = User()
        self.user.username = 'testuser'
        self.user.email = 'testuser@testuser.com'
        self.user.set_password('testuser')
        self.user.save()
        self.profile = Profile()
        self.profile.user = self.user
        self.profile.language = 'en'
        self.profile.save()
        self.user2 = User()
        self.user2.username = 'testuser2'
        self.user2.email = 'testuser2@testuser.com'
        self.user2.set_password('testuser2')
        self.user2.save()
        self.profile2 = Profile()
        self.profile2.user = self.user2
        self.profile2.language = 'en'
        self.profile2.save()

        self.auction = Auction.objects.get(title='title 1')
        self.bannedAuction = Auction.objects.get(title='title 2')
        self.bannedAuction.status = 'Banned'
        self.bannedAuction.save()

    # Test to check user cannot bid on auction without authentication
    def testPlaceBidWithoutAuthentication(self):
        prevcount = Bid.objects.count()
        auction_id = str(self.auction.id)
        bid_revision = str(self.auction.revision)
        bid_amount = round(self.auction.starting_price + Decimal(0.01),2)
        resp = self.client.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevcount, Bid.objects.count())

    # Test to check that bid can be placed successfully on auctions using authenticated user (provided that all validation are passed)
    def testPlaceBidWithAuthenticationSuccesfully(self):
        # Login
        self.client.login(username='testuser', password='testuser')
        # Place bid
        prevcount = Bid.objects.count()
        auction_id = str(self.auction.id)
        bid_revision = str(self.auction.revision)
        bid_amount = round(self.auction.starting_price + Decimal(0.01), 2)
        resp = self.client.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevcount + 1, Bid.objects.count())

    # Test to check that bid fails if bid amount is equal to current price/bid of auction
    def testFailBidDueToEqualThanStartPrice(self):
        # Login
        self.client.login(username='testuser', password='testuser')
        # Place bid
        prevCount = Bid.objects.count()
        auction_id = str(self.auction.id)
        bid_revision = str(self.auction.revision)
        bid_amount = round(self.auction.starting_price, 2)
        resp = self.client.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount, Bid.objects.count())

    # Test to check that bid fails if bid amount is less to current price/bid of auction
    def testFailBidDueToLessThanStartPrice(self):
        # Login
        self.client.login(username='testuser', password='testuser')
        # Place bid
        prevCount = Bid.objects.count()
        auction_id = str(self.auction.id)
        bid_revision = str(self.auction.revision)
        bid_amount = round(self.auction.starting_price - Decimal(0.01), 2)
        resp = self.client.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount, Bid.objects.count())

    # Test to check that bid fails if user is already the highest bidder
    def testFailBidDueToAlreadyWinning(self):
        # Login
        self.client.login(username='testuser', password='testuser')
        # Place bid
        prevCount = Bid.objects.count()
        auction_id = str(self.auction.id)
        bid_revision = str(self.auction.revision)
        bid_amount = round(self.auction.starting_price + Decimal(0.01), 2)
        resp = self.client.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount+1, Bid.objects.count())
        prevCount = Bid.objects.count()
        bid_amount = round(bid_amount + Decimal(0.01), 2)
        resp = self.client.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount, Bid.objects.count())

    # Test to check that bid fails if bidder is equal to seller
    def testFailBidDueToBidderEqualToSeller(self):
        # Login
        self.client.login(username='user1', password='pass1')
        # Place bid
        prevCount = Bid.objects.count()
        auction_id = str(self.auction.id)
        bid_revision = str(self.auction.revision)
        bid_amount = round(self.auction.starting_price + Decimal(0.01), 2)
        resp = self.client.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount, Bid.objects.count())

    # Test to check that bid fails if user tries to bid on non-active auction
    def testFailBidDueToNonActiveAuction(self):
        # Login
        self.client.login(username='user1', password='pass1')
        # Place bid
        prevCount = Bid.objects.count()
        auction_id = str(self.bannedAuction.id)
        bid_revision = str(self.bannedAuction.revision)
        bid_amount = round(self.bannedAuction.starting_price + Decimal(0.01), 2)
        resp = self.client.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount, Bid.objects.count())

    # Test to check concurrency that user cannot bid if description of auction is updated in background
    def testBidConcurrencyForDescriptionUpdate(self):
        # Login

        c1 = Client()
        c1.login(username='testuser', password='testuser')

        # user gets version of auction
        oldAuction = self.auction

        # self.auction is updated by user using non-login token

        resp = self.client.post(reverse('auctions:auction-edit-without', args=(self.auction.edit_token,)),
                        {'description': 'Description2'
                         })

        # user tries to bid on old version
        prevCount = Bid.objects.count()
        auction_id = str(oldAuction.id)
        bid_revision = str(oldAuction.revision)
        bid_amount = round(oldAuction.starting_price + Decimal(0.01), 2)
        resp = c1.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount, Bid.objects.count())

    # Test to check concurrency that bid fails if some other user bids on auction in meantime and that bid is greater than user's bid
    def testBidConcurrencyForAnotherUserBid(self):
        # Login
        c1 = Client()
        c1.login(username='testuser', password='testuser')
        c2 = Client()
        c2.login(username='testuser2', password='testuser2')

        # user 1 bids on auction
        prevCount = Bid.objects.count()
        auction_id = str(self.auction.id)
        bid_revision = str(self.auction.revision)
        bid_amount = round(self.auction.starting_price + Decimal(0.01), 2)
        if self.auction.bid_price:
            bid_amount = round(self.auction.bid_price + Decimal(0.01), 2)
        resp = c1.post(reverse('auctions:bid', args=(auction_id,)),
                                {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount + 1, Bid.objects.count())

        # user 2 tries to bid on same auction using same details (not updated yet from database)
        prevCount = Bid.objects.count()
        resp = c2.post(reverse('auctions:bid', args=(auction_id,)),
                       {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount, Bid.objects.count())

        # user 2 gets updated auction and then bids with higher amount
        prevCount = Bid.objects.count()
        self.auction = Auction.objects.get(title='title 1')
        auction_id = str(self.auction.id)
        bid_revision = str(self.auction.revision)
        bid_amount = round(self.auction.starting_price + Decimal(0.01), 2)
        if self.auction.bid_price:
            bid_amount = round(self.auction.bid_price + Decimal(0.01), 2)
        resp = c2.post(reverse('auctions:bid', args=(auction_id,)),
                       {'revision': bid_revision, 'bid_amount': bid_amount})
        self.assertEqual(prevCount + 1, Bid.objects.count())

