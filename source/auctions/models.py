from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator


# Model for saving user language preference
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    language = models.CharField(max_length=10, default='en')


# Model for saving currency values from api
class Currency(models.Model):
    currency = models.CharField(max_length=10)
    value = models.DecimalField(max_digits=19, decimal_places=4)


# Model for saving auction data
class Auction(models.Model):
    STATUS__CHOICES = (
        ('Active', 'Active'),
        ('Banned', 'Banned'),
        ('Due', 'Due'),
        ('Adjudicated', 'Adjudicated'),
    )
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=500)
    description = models.CharField(max_length=4000)
    currency = models.CharField(max_length=10)
    edit_token = models.CharField(max_length=500)
    starting_price = models.DecimalField(max_length=30, max_digits=19, decimal_places=2)
    bid_price = models.DecimalField(max_length=30, max_digits=19, decimal_places=2, null=True)
    winner_id = models.IntegerField(null=True)
    start_date = models.DateTimeField(blank=True)
    duration_hours = models.IntegerField(default=72, validators=[MinValueValidator(72)])
    end_date = models.DateTimeField(blank=True)
    status = models.CharField(max_length=15, choices=STATUS__CHOICES, default='Active')
    revision = models.IntegerField(default=1)

    def __str__(self):
        return self.title


# Model for saving bid data
class Bid(models.Model):
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    bid_amount = models.DecimalField(max_length=30, max_digits=19, decimal_places=2)
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)

    def __str__(self):
        return self.bidder.username