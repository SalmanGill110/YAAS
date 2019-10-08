from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from auctions.models import Profile
from django.contrib.auth import authenticate, login, logout
from .forms import UserForm, LoginForm, UserEditForm
from django.views.generic import View
from django.contrib.auth.decorators import login_required
from auctions.views import language_folder_selection


# Create user
class UserFormView(View):
    form_class = UserForm

    def get(self, request):
        template_name = 'auctions/' + language_folder_selection(request) + 'registration_form.html'
        form = self.form_class(None)
        return render(request, template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        template_name = 'auctions/' + language_folder_selection(request) + 'registration_form.html'
        if form.is_valid():
            user = form.save(commit=False)
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user.set_password(password)
            user.save()
            profile = Profile()
            profile.language = 'en'
            profile.user = user
            profile.save()
            user = authenticate(username=username, password=password)

            if user is not None:

                if user.is_active:
                    login(request, user)
                    request.session['language'] = User.objects.get(pk=user.id).profile.language
                    return redirect('auctions:index')

        return render(request, template_name, {'form': form})


# Edit user details
class UserEditFormView(LoginRequiredMixin, View):
    login_url = 'users:login'
    redirect_field_name = 'redirect_to'
    form_class = UserEditForm

    def get(self, request):
        template_name = 'auctions/' + language_folder_selection(request) + 'registration_edit_form.html'
        form = self.form_class(None)
        form.fields['email'].initial = request.user.email
        return render(request, template_name, {'form': form})

    def post(self, request):
        form = self.form_class(request.POST)
        template_name = 'auctions/' + language_folder_selection(request) + 'registration_edit_form.html'

        if form.is_valid():
            db_user = User.objects.get(pk=request.user.id)
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            db_user.email = user.email
            if password == form.cleaned_data['confirm_password']:
                db_user.set_password(password)
                db_user.save()
                logout(request)
                return redirect('users:login')
            return render(request, template_name, {'form': form, 'error_message': "Both passwords doesn't match"})
        return render(request, template_name, {'form': form})


# Login user
class LoginFormView(View):
    form_class = LoginForm

    def get(self, request):
        template_name = 'auctions/' + language_folder_selection(request) + 'login_form.html'
        form = self.form_class(None)
        return render(request, template_name, {'form': form})

    def post(self, request):
        template_name = 'auctions/' + language_folder_selection(request) + 'login_form.html'
        form = self.form_class(request.POST)
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(username=username, password=password)

        if user is not None:

            if user.is_active:
                login(request, user)
                try:
                    language = User.objects.get(pk=user.id).profile.language
                except:
                    profile = Profile()
                    profile.language = 'en'
                    profile.user = User.objects.get(pk=user.id)
                    profile.save()
                request.session['language'] = User.objects.get(pk=user.id).profile.language
                query = request.POST.get('next')
                if query:
                    return redirect(query)
                return redirect('auctions:index')

        return render(request, template_name, {'form': form, 'error_message': "Invalid credentials"})


# Logout user
@login_required(login_url='users:login')
def logout_user(request):
    logout(request)
    return redirect('auctions:index')
