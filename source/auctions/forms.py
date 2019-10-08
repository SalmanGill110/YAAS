from django import forms
from .models import Auction, Bid


class AuctionForm(forms.ModelForm):

    class Meta:
        model = Auction
        fields = ['title', 'description', 'starting_price', 'duration_hours']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class EditAuctionForm(forms.ModelForm):

    class Meta:
        model = Auction
        fields = ['description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }

class BidForm(forms.ModelForm):

    class Meta:
        model = Bid
        fields = ['bid_amount']
