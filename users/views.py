from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Address

def login_user(request):
    username_input = ''
    if request.method == 'POST':
        username_input = request.POST.get('username', '')
        password_input = request.POST.get('password', '')
        user = authenticate(request, username=username_input, password=password_input)
        
        if user is not None:
            login(request, user)
            return redirect('items:show_marketplace')
        else:
            messages.error(request, "Invalid username or password.")
            
    return render(request, 'login.html', {'username': username_input})

def register_user(request):
    if request.method == 'POST':
        username_input = request.POST.get('username', '')
        email_input = request.POST.get('email', '')
        password_input = request.POST.get('password', '')

        context = {
            'username': username_input,
            'email': email_input,
            'password': password_input,
        }

        if not username_input or not email_input or not password_input:
            messages.error(request, "Please fill in all required fields.")
            return render(request, 'register.html', context)

        if '@' not in email_input:
            messages.error(request, "Email must contain '@' character.")
            return render(request, 'register.html', context)

        if User.objects.filter(username=username_input).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'register.html', context)

        if len(password_input) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'register.html', context)
        
        if not any(char.isupper() for char in password_input):
            messages.error(request, "Password must contain at least 1 uppercase letter (A-Z).")
            return render(request, 'register.html', context)
        
        if not any(not char.isalpha() for char in password_input):
            messages.error(request, "Password must contain at least 1 number or special character.")
            return render(request, 'register.html', context)

        user = User.objects.create_user(username=username_input, email=email_input, password=password_input)
        user.save()
        messages.success(request, "Account created successfully! Please log in.")
        return redirect('login')
            
    return render(request, 'register.html')

def logout_user(request):
    logout(request)
    return redirect('items:show_marketplace')

@login_required(login_url='/login/')
def profile_view(request):
    addresses = Address.objects.filter(user=request.user).order_by('-is_primary', '-id')
    return render(request, 'profile.html', {'addresses': addresses})

@login_required(login_url='/login/')
def add_address(request):
    if request.method == 'POST':
        recipient_name = request.POST.get('recipient_name')
        phone_number = request.POST.get('phone_number')
        full_address = request.POST.get('full_address')
        city_province_postal = request.POST.get('city_province_postal')
        is_primary = request.POST.get('is_primary') == 'on'

        if is_primary:
            Address.objects.filter(user=request.user, is_primary=True).update(is_primary=False)

        Address.objects.create(
            user=request.user,
            recipient_name=recipient_name,
            phone_number=phone_number,
            full_address=full_address,
            city_province_postal=city_province_postal,
            is_primary=is_primary
        )
        messages.success(request, "Address successfully added!")
    return redirect('profile')

@login_required(login_url='/login/')
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.delete()
    messages.success(request, "Address successfully deleted!")
    return redirect('profile')