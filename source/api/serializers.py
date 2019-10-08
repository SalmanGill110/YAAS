from rest_framework import serializers
from auctions.models import Auction, Bid


class Others(object):
    def __init__(self, hours, minutes):
        self.hours = hours
        self.minutes = minutes


# Serializer for auction model
class AuctionSerializer(serializers.ModelSerializer):
    bid_set = serializers.StringRelatedField(many=True)
    seller = serializers.ReadOnlyField(source='seller.username')

    class Meta:
        model = Auction
        fields = ('id', 'title', 'description', 'revision', 'starting_price', 'bid_price', 'currency', 'end_date', 'seller', 'bid_set')


# Serializer for multiple auctions
class AuctionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Auction
        fields = ('id', 'title', 'end_date')


# Serializer for some other data
class OthersSerializer(serializers.Serializer):
    hours = serializers.IntegerField()
    minutes = serializers.IntegerField()
