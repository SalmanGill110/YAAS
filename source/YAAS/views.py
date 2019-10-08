from django.shortcuts import render
from django.http import HttpResponse
from auctions.models import Auction, Profile, Bid
from django.contrib.auth.models import User
from YAAS import DBPopulate


def index(request):
    return render(request, 'YAAS/index.html')


# Populate database
def populate_db(request):
    # Empty Database
    Profile.objects.all().delete()
    Bid.objects.all().delete()
    Auction.objects.all().delete()
    User.objects.all().delete()
    # Create super user
    u = User(username='admin')
    u.set_password('Easports')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    profile = Profile()
    profile.language = 'en'
    profile.user = User.objects.get(pk=u.id)
    profile.save()
    # Populate data in database
    database = DBPopulate.DBPopulator()
    database.populate()
    return HttpResponse('Created Successfully...')


# Populate database for tests
def populate_test_db():
    # Empty Database
    Profile.objects.all().delete()
    Bid.objects.all().delete()
    Auction.objects.all().delete()
    User.objects.all().delete()
    # Create super user
    u = User(username='admin')
    u.set_password('Easports')
    u.is_superuser = True
    u.is_staff = True
    u.save()
    profile = Profile()
    profile.language = 'en'
    profile.user = User.objects.get(pk=u.id)
    profile.save()
    # Populate data in database
    database = DBPopulate.DBPopulator()
    database.populate()
