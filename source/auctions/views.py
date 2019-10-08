from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.views.generic import View
from .models import Auction, Bid, Profile, Currency
from .forms import AuctionForm, EditAuctionForm, BidForm
from django.utils import timezone
from datetime import datetime, timedelta
from django.utils.crypto import get_random_string
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
import threading
import requests
from decimal import Decimal
import time


# Options for currency selection in template and returned from api
currency_options = [{'name':'Australian Dollar','value':'AUD'},
{'name':'Euros','value':'EUR'},
{'name':'Bulgarian Lev','value':'BGN'},
{'name':'Brazilian Real','value':'BRL'},
{'name':'Canadian Dollar','value':'CAD'},
{'name':'Swiss Franc','value':'CHF'},
{'name':'Renminbi(Yuan)','value':'CNY'},
{'name':'Czech Koruna','value':'CZK'},
{'name':'Danish Krone','value':'DKK'},
{'name':'Pound Sterling','value':'GBP'},
{'name':'HK Dollar','value':'HKD'},
{'name':'Croatian Kuna','value':'HRK'},
{'name':'Forint','value':'HUF'},
{'name':'Rupiah','value':'IDR'},
{'name':'Israeli Sheqel','value':'ILS'},
{'name':'Indian Rupee','value':'INR'},
{'name':'Yen','value':'JPY'},
{'name':'Won','value':'KRW'},
{'name':'Mexican Peso','value':'MXN'},
{'name':'Malaysian Ringgit','value':'MYR'},
{'name':'Norwegian Krone','value':'NOK'},
{'name':'NZ Dollar','value':'NZD'},
{'name':'Philippine Peso','value':'PHP'},
{'name':'Zloty','value':'PLN'},
{'name':'Russian Ruble','value':'RUB'},
{'name':'Swedish Krona','value':'SEK'},
{'name':'Singapore Dollar','value':'SGD'},
{'name':'Thai Baht','value':'THB'},
{'name':'Turk Lira','value':'TRY'},
{'name':'US Dollar','value':'USD'},
{'name':'Rand','value':'ZAR'}]


# Get currency value prices from database
def currency_exchange(currency):
    currency_val = 1.0000
    if currency != 'EUR':
        if Currency.objects.filter(currency=currency).exists():
            curr = Currency.objects.get(currency=currency)
            currency_val = float(curr.value)
    return currency_val


# Change language for user and save preference in database if user is authenticated
@csrf_exempt
def change_language(request):
    query = request.POST.get("lang")
    if (query == ''):
        return redirect('auctions:index')
    if (query == 'en' or query == 'sv' or query == 'fi'):
        request.session['language'] = query
        if request.user.is_authenticated():
            user = User.objects.get(pk=request.user.id)
            profile = Profile.objects.get(user=user)
            profile.language = query
            profile.save()
    return redirect('auctions:index')


# Folder selection based on language
def language_folder_selection(request):
    language = ''
    if 'language' in request.session:
        language = request.session['language']
    if language == 'fi':
        language = 'fi/'
    if language == 'sv':
        language = 'sv/'
    if language == 'en':
        language = ''
    return language


# Decide header based on user authentication
def get_base_template(request):
    if request.user.is_authenticated():
        base_template = "auctions/base.html"
    else:
        base_template = "auctions/base_visitor.html"
    return base_template


# Browse 10 latest auctions or searched auctions
def index(request):
    base_template = get_base_template(request)
    query = request.GET.get("q")
    if query:
        auctions = Auction.objects.filter(title__icontains=query, status='Active').distinct().order_by('-id')
        return render(request, 'auctions/'+language_folder_selection(request)+'index.html', {'object_list': auctions, 'heading': "Searched Auctions", 'base_template': base_template})
    else:
        auctions = Auction.objects.filter(status='Active').order_by('-id')[:10]
        return render(request, 'auctions/'+language_folder_selection(request)+'index.html', {'object_list': auctions, 'heading': "Latest Auctions", 'base_template': base_template})


# Browse all auctions
def browse(request):
    base_template = get_base_template(request)
    auctions = Auction.objects.filter(status='Active').order_by('-id')
    return render(request,  'auctions/'+language_folder_selection(request)+'index.html', {'object_list': auctions, 'heading': "Auctions", 'base_template': base_template})


# Browse banned auctions - admin(super) user only
def browse_banned(request):
    if not request.user.is_superuser:
        return HttpResponse('You are not authorized to perform this action')
    base_template = get_base_template(request)
    auctions = Auction.objects.filter(status='Banned').order_by('-id')
    return render(request, 'auctions/'+language_folder_selection(request)+'index.html', {'object_list': auctions, 'heading': "Banned Auctions", 'base_template': base_template})


# Browse auctions listed by user
@login_required(login_url='users:login')
def my_auctions(request):
    base_template = get_base_template(request)
    auctions = Auction.objects.filter(seller_id=request.user.pk, status='Active').order_by('-id')[:10]
    return render(request, 'auctions/'+language_folder_selection(request)+'index.html', {'object_list': auctions, 'heading': "My Auctions", 'base_template': base_template})


# Details of an auction
def detail(request, auction_id):
    query = request.GET.get("curr")
    currency = 'EUR'
    if query:
        currency = query
        request.session['project'] = currency
    else:
        if 'project' in request.session:
            currency = request.session['project']
    currency_val = currency_exchange(currency)
    auction = get_object_or_404(Auction, pk=auction_id, status='Active')
    auction.bid_set.all()
    diff = auction.end_date - timezone.now()
    seconds = diff.total_seconds()
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    context = {
        'auction': auction,
        'hours': hours,
        'minutes': minutes,
        'base_template': get_base_template(request),
        'currency_options': currency_options,
        'currency': currency,
        'currency_val': currency_val}
    return render(request, 'auctions/'+language_folder_selection(request)+'details.html', context)


# Get data from forum and save in session storage, then redirect to confirmation page
@login_required(login_url='users:login')
def create_auction(request):
        form = AuctionForm(request.POST or None, request.FILES or None)
        if form.is_valid():
            context = {
                "form": form,
                'base_template': "auctions/base.html",
            }
            auction = form.save(commit=False)
            save_into_session(request, auction)
            return render(request, 'auctions/'+language_folder_selection(request)+'auction_confirmation_form.html', context)
        context = {
           "form": form,
            'base_template': "auctions/base.html",
        }
        return render(request, 'auctions/'+language_folder_selection(request)+'auction_form.html', context)


# On user confirmation get data from session storage and save in database
@login_required(login_url='users:login')
def confirm_auction(request):
        if request.method == 'POST':
            if (request.POST['confirm'] == 'True'):
                auction = get_from_session(request)
                auction.seller = request.user
                auction.start_date = timezone.now()
                auction.end_date = auction.start_date + timedelta(hours=auction.duration_hours)
                auction.edit_token =  auction.start_date.strftime('%Y%m%d%H%M%S') + get_random_string()
                auction.revision = 1
                auction.save()
                subject = 'Auction is created'
                body = 'It is to inform that Auction with title "' + auction.title + '" has been created on YAAS'
                body += '\nyou can see the description of created auction by following link '
                body += '\n' + request.get_host() + '/auctions/' + str(auction.id) + '/'
                body += '\nyou can edit description of auction by using following link '
                body += '\n' + request.get_host() + '/auctions/auction/non/edit/'+ auction.edit_token + '/'
                email = EmailMessage(subject, body, from_email='no-reply@yaas.com', to=['user@yaas.com'])
                email.send()
                return redirect('auctions:index')
        return redirect('auctions:index')


# Edit auction description without signing in
class AuctionEditFormNonView(View):
    form_class = EditAuctionForm
    def get(self, request, edit_token):
        template_name = 'auctions/' + language_folder_selection(request) + 'auction_form.html'
        form = self.form_class(None)
        num_results = Auction.objects.filter(edit_token=edit_token).count()
        if num_results > 0:
            auction = Auction.objects.get(edit_token=edit_token)
            form.fields['description'].initial = auction.description
            return render(request, template_name, {'form': form, 'base_template': get_base_template(request)})
        return redirect('auctions:index')
    def post(self, request, edit_token):
        template_name = 'auctions/' + language_folder_selection(request) + 'auction_form.html'
        form = self.form_class(request.POST)
        if form.is_valid():
            db_auction = Auction.objects.get(edit_token=edit_token)
            db_auction.description = form.cleaned_data['description']
            db_auction.revision = db_auction.revision + 1
            db_auction.save()
            return redirect('auctions:index')
        return render(request, template_name, {'form': form, 'base_template': get_base_template(request)})


# Edit auction description with authenticated user
class AuctionEditFormView(LoginRequiredMixin, View):
    login_url = 'users:login'
    redirect_field_name = 'redirect_to'
    form_class = EditAuctionForm

    def get(self, request, pk):
        template_name = 'auctions/' + language_folder_selection(request) + 'auction_form.html'
        form = self.form_class(None)
        num_results = Auction.objects.filter(pk=pk).count()
        if num_results > 0:
            auction = Auction.objects.get(pk=pk)
            form.fields['description'].initial = auction.description
            if request.user != auction.seller:
                return HttpResponse('You are not authorized to perform this action')
            return render(request, template_name, {'form': form, 'base_template': "auctions/base.html"})
        return redirect('auctions:index')

    def post(self, request, pk):
        template_name = 'auctions/' + language_folder_selection(request) + 'auction_form.html'
        form = self.form_class(request.POST)
        if form.is_valid():
            db_auction = Auction.objects.get(pk=pk)
            db_auction.description = form.cleaned_data['description']
            db_auction.revision = db_auction.revision + 1
            db_auction.save()
            return redirect('auctions:index')
        return render(request, template_name, {'form': form, 'base_template': "auctions/base_visitor.html"})


# Ban an auction - admin(super) user only
def auction_ban(request, pk):
    if request.user.is_superuser:
        auction  = Auction.objects.get(id=pk)
        auction.status = "Banned"
        auction.save()
        send_ban_email(pk)
    else:
        return HttpResponse("HTTP 403 Forbidden : You need admin privileges to access this functionality", status=403)
    return redirect('auctions:index')


# Un-ban an auction - admin(super) user only
def auction_unban(request, pk):
    if request.user.is_superuser:
        auction  = Auction.objects.get(id=pk, status='Banned')
        auction.status = "Active"
        auction_delta = auction.end_date - timezone.now()
        expiry_check = auction_delta.total_seconds()
        if (expiry_check < 0):
            auction.status = "Due"
        auction.save()
    else:
        return HttpResponse("HTTP 403 Forbidden : You need admin privileges to access this functionality", status=403)
    return redirect('auctions:index')


# Bid validation factors
def verify_bid(user, auction, bid_revision, bid_amount):
    if (bid_revision != auction.revision):
        return 'Description of Auction updated by seller, please read again before submitting bid.'
    if (auction.bid_price):
        if (bid_amount <= auction.bid_price):
            return 'Please bid higher then current price'
    if (bid_amount <= auction.starting_price):
        return 'Please bid higher then current price'
    if (auction.winner_id == user.pk):
        return 'You are already highest bidder'
    if (auction.seller.pk == user.pk):
        return 'You cannot bid on your own auction'
    auction_delta = auction.end_date - timezone.now()
    expiry_check = auction_delta.total_seconds()
    if (expiry_check < 0):
        return 'Auction Expired : better luck next time !!!!'
    if (auction.status != 'Active'):
        return 'Auction Not Available !!!!'
    return ''


# Bid on an auction
class BidFormFormView(LoginRequiredMixin, View):
    login_url = 'users:login'
    redirect_field_name = 'redirect_to'
    form_class = BidForm

    def get(self, request, auction_id):
        template_name = 'auctions/' + language_folder_selection(request) + 'bid.html'
        form = self.form_class(None)
        auction = get_object_or_404(Auction, pk=auction_id)
        return render(request, template_name, {'form': form, 'auction': auction})

    def post(self, request, auction_id):
        template_name = 'auctions/' + language_folder_selection(request) + 'bid.html'
        auction = Auction.objects.get(pk=auction_id)
        form = self.form_class(request.POST)
        print(form.errors)
        if form.is_valid():
            bid = form.save(commit=False)
            bid_revision = int(request.POST['revision'])
            bid_amount = form.cleaned_data['bid_amount']

            auction_delta = auction.end_date - timezone.now()
            expiry_check = auction_delta.total_seconds()
            hours = int(expiry_check // 3600)
            minutes = int((expiry_check % 3600) // 60)
            error_message = verify_bid(request.user, auction, bid_revision, bid_amount)
            if error_message != '':
                return render(request, template_name,
                              {'form': form, 'auction': auction, 'error_message': error_message})
            bid.bid_amount = bid_amount
            bid.auction = auction
            bid.bidder = request.user
            bid_count = Bid.objects.filter(auction=auction, bidder=request.user).count()
            if(bid_count>0):
                bid2 = Bid.objects.get(auction=auction, bidder=request.user)
                bid2.bid_amount= bid_amount
                bid2.save()
            else:
                bid.save()
            # Soft deadlines
            if(hours==0 and minutes<5):
                auction.end_date = auction.end_date + timedelta(minutes=5)

            auction.bid_price = bid_amount
            auction.winner_id = request.user.pk
            auction.save()
            # Send email to stakeholders on auction on bid event
            send_bid_email(auction_id)
            return redirect('auctions:index')
        return render(request, template_name, {'form': form, 'auction': auction})


# Send email to stakeholders on auction on bid event
def send_bid_email(auction_id):
    auction = Auction.objects.get(pk=auction_id)
    bids = Bid.objects.filter(auction=auction)
    to = [auction.seller.email]
    new_bidder = ''
    for bid in bids:
        to.append(bid.bidder.email)
        if bid.bidder.id == auction.winner_id:
            new_bidder = bid.bidder.username

    subject = 'A new bid'
    body = 'It is to inform that Auction with title "' + auction.title + '" has a new bid on YAAS'
    body += '\nNew Bid amount is = ' + str(auction.bid_price) + ''
    body += '\nAnd the bidder is = ' + new_bidder + ''
    email = EmailMessage(subject, body, from_email='no-reply@yaas.com', to=to)
    email.send()


# Send email to stakeholders for auction on ban event
def send_ban_email(auction_id):
    auction = Auction.objects.get(pk=auction_id)
    to = [auction.seller.email]
    bid_count = Bid.objects.filter(auction=auction).count()
    if bid_count > 0:
        bids = Bid.objects.filter(auction=auction)
        for bid in bids:
            to.append(bid.bidder.email)

    subject = 'Auction is Banned by Admin'
    body = 'It is to inform that Auction with title "' + auction.title + '" has been banned by Admin'
    body += '\nIf you require more information regarding this, You can contact support center'
    email = EmailMessage(subject, body, from_email='no-reply@yaas.com', to=to)
    email.send()


# Send email to stakeholders for auction on resolve event
def send_resolve_email(auction_id):
    auction = Auction.objects.get(pk=auction_id)
    bid_count = Bid.objects.filter(auction=auction).count()
    if bid_count > 0:
        bids = Bid.objects.filter(auction=auction)
        to = [auction.seller.email]
        winner = User.objects.get(pk=auction.winner_id).username
        for bid in bids:
            to.append(bid.bidder.email)
        subject = 'Auction is Adjudicated'
        body = 'It is to inform that Auction with title "' + auction.title + '" has a been Adjudicated'
        body += '\nWinning Bid amount is = ' + str(auction.bid_price) + ''
        body += '\nAnd Winner is = ' + winner + ''
        email = EmailMessage(subject, body, from_email='no-reply@yaas.com', to=to)
        email.send()
    else:
        to = [auction.seller.email]
        subject = 'Auction is Adjudicated'
        body = 'It is to inform that Auction with title "' + auction.title + '" has a been Adjudicated'
        body += '\nUnfortunately auction was expired without any bids...'
        email = EmailMessage(subject, body, from_email='no-reply@yaas.com', to=to)
        email.send()


# save keys in session rather then object because decimal and datetime fields cannot be serialized by default serializer
def save_into_session(request, auction):
    request.session['title'] = auction.title
    request.session['description'] = auction.description
    request.session['starting_price'] = str(auction.starting_price)
    request.session['duration_hours'] = auction.duration_hours


def get_from_session(request):
    auction = Auction()
    auction.title = request.session['title']
    auction.description = request.session['description']
    auction.duration_hours = request.session['duration_hours']
    auction.starting_price = Decimal(request.session['starting_price'])
    del request.session['title']
    del request.session['description']
    del request.session['duration_hours']
    del request.session['starting_price']
    return auction


# Threaded Deamonized tasks for auto resolving of bid and getting data from api for currency values
class Threading(object):

    def __init__(self):

        thread = threading.Thread(target=self.put_into_due, args=())
        thread.daemon = True                            # Daemonize thread
        thread.start()                                  # Start the execution

        thread2 = threading.Thread(target=self.resolve_auction, args=())
        thread2.daemon = True  # Daemonize thread
        thread2.start()

        thread3 = threading.Thread(target=self.currency_exchange_from_api, args=())
        thread3.daemon = True  # Daemonize thread
        thread3.start()

    # Runs every 60 seconds to check if there is any auction to be put in due status
    def put_into_due(self):
        while True:
            auctions = Auction.objects.filter(status='Active', end_date__lt=timezone.now())
            for auction in auctions:
                auction.status = 'Due'
                auction.save()
            time.sleep(60)

    # Runs every 5 minutes to adjudicate auctions
    def resolve_auction(self):
        while True:
            auctions = Auction.objects.filter(status='Due', end_date__lt=timezone.now())
            for auction in auctions:
                auction.status = 'Adjudicated'
                auction.save()
                send_resolve_email(auction.id)
            time.sleep(300)

    # Run every 10 minutes to get Latest Prices from currency exchange
    def currency_exchange_from_api(self):
        while True:
            request_string = 'http://api.fixer.io/latest'
            temp = requests.get(request_string)
            json_data = temp.json()
            for option in currency_options:
                currency = option.get('value')
                if currency != 'EUR':
                    currency_val = json_data['rates'][currency]
                    if Currency.objects.filter(currency=currency).exists():
                        curr = Currency.objects.get(currency=currency)
                        curr.value = currency_val
                        curr.save()
                    else:
                        curr = Currency()
                        curr.currency = currency
                        curr.value = currency_val
                        curr.save()
            time.sleep(600)


Task = Threading()
