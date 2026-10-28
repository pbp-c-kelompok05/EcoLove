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
            messages.error(request, "Username atau password salah.")
            
    return render(request, 'login.html', {'username': username_input})

def register_user(request):
    if request.method == 'POST':
        username_input = request.POST.get('username')
        email_input = request.POST.get('email')
        password_input = request.POST.get('password')
        
        # 1. Cek apakah username sudah ada
        if User.objects.filter(username=username_input).exists():
            messages.error(request, "Username sudah digunakan.")
            return render(request, 'register.html')

        # 2. Validasi Ketentuan Password
        if len(password_input) < 8:
            messages.error(request, "Password harus minimal 8 karakter.")
            return render(request, 'register.html')
        
        if not any(char.isupper() for char in password_input):
            messages.error(request, "Password harus mengandung minimal 1 huruf kapital (A-Z).")
            return render(request, 'register.html')
        
        if not any(not char.isalpha() for char in password_input):
            messages.error(request, "Password harus mengandung minimal 1 angka atau karakter unik (seperti . , ! @ 1 2).")
            return render(request, 'register.html')

        # 3. Buat akun jika semua syarat terpenuhi
        user = User.objects.create_user(username=username_input, email=email_input, password=password_input)
        user.save()
        messages.success(request, "Akun berhasil dibuat! Silakan login.")
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