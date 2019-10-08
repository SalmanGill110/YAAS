from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from auctions.models import Auction, Bid
from .serializers import AuctionsSerializer, AuctionSerializer, Others, OthersSerializer
from datetime import datetime, timedelta
from rest_framework.decorators import parser_classes
from rest_framework.parsers import JSONParser
from auctions.views import send_bid_email, verify_bid
from django.contrib.auth import authenticate
from decimal import Decimal
import base64


# List of auctions
class AuctionsList(APIView):

    def get(self, request):
        auctions = None
        query1 = request.GET.get("count")
        query2 = request.GET.get("title")
        if query1 and not query2:
            auctions = Auction.objects.filter(status='Active').distinct().order_by('-id')[:int(query1)]
        if query2 and not query1:
            auctions = Auction.objects.filter(title__icontains=query2, status='Active').distinct().order_by('-id')
        if not query1 and not query2:
            auctions = Auction.objects.filter(status='Active').order_by('-id')
        if query1 and query2:
            auctions = Auction.objects.filter(title__icontains=query2, status='Active').distinct().order_by('-id')[:int(query1)]

        serializer = AuctionsSerializer(auctions, many=True)
        return Response(serializer.data)

    def post(self):
        pass


# Auction details
class AuctionDetails(APIView):

    def get(self, request, auction_id):
        auction = get_object_or_404(Auction, pk=auction_id, status='Active')
        auction.currency = "EUR"
        serializer = AuctionSerializer(auction, many=False)
        diff = auction.end_date.replace(tzinfo=None) - datetime.now()
        seconds = diff.total_seconds()
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        other = Others(hours=hours, minutes=minutes)
        serializer2 = OthersSerializer(other, many=False)

        return Response({'auction_details': serializer.data,
        'time_remaining': serializer2.data,
    })


# Bid on an auction
class BidOnAuction(APIView):
    @parser_classes((JSONParser,))
    def post(self, request, auction_id):
        auth_info = self.request.META.get("HTTP_AUTHORIZATION", None)
        if auth_info and auth_info.startswith("Basic "):
            basic_info = auth_info.split(" ", 1)[1]
            temp = base64.b64decode(basic_info)
            str = bytes.decode(temp)
            username, password = str.split(":")
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    revision = ''
                    bid_amount = 0.00
                    try:
                        data = request.data
                        revision = data['revision']
                        bid_amount = round(Decimal.from_float(data['my_bid']), 2)
                    except:
                        return Response({'detail': 'There is something wrong with your request format'}, status.HTTP_406_NOT_ACCEPTABLE)

                    if Auction.objects.filter(pk=auction_id, status='Active').exists():
                        auction = Auction.objects.get(pk=auction_id)
                        error_message = verify_bid(user, auction, revision, bid_amount)
                        auction_delta = auction.end_date.replace(tzinfo=None) - datetime.now()
                        expiry_check = auction_delta.total_seconds()
                        hours = int(expiry_check // 3600)
                        minutes = int((expiry_check % 3600) // 60)
                        if error_message !='':
                            return Response({'detail': error_message}, status.HTTP_406_NOT_ACCEPTABLE)
                        bid = Bid()
                        bid.bid_amount = bid_amount
                        bid.auction = auction
                        bid.bidder = user
                        bid_count = Bid.objects.filter(auction=auction, bidder=user).count()
                        if (bid_count > 0):
                            bid2 = Bid.objects.get(auction=auction, bidder=user)
                            bid2.bid_amount = bid_amount
                            bid2.save()
                        else:
                            bid.save()
                        # Soft deadlines
                        if (hours == 0 and minutes < 5):
                            auction.end_date = auction.end_date + timedelta(minutes=5)
                        auction.bid_price = bid_amount
                        auction.winner_id = user.pk
                        auction.save()
                        # Send email to stakeholders on auction on bid event
                        send_bid_email(auction_id)

                        return Response({'detail': 'Successful'}, status.HTTP_200_OK)
                    else:
                        return Response({'detail': 'No active auction with provided id exists'},
                                        status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({'detail': 'Authorization failed'}, status.HTTP_403_FORBIDDEN)
            else:
                return Response({'detail': 'Authorization failed'}, status.HTTP_403_FORBIDDEN)
        else:
            return Response({'detail': 'Authorization Missing'}, status.HTTP_403_FORBIDDEN)
