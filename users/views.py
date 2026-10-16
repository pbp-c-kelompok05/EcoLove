from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def login_user(request):
    username_input = ''
    if request.method == 'POST':
        username_input = request.POST.get('username', '')
        password_input = request.POST.get('password', '')
        user = authenticate(request, username=username_input, password=password_input)
        
        if user is not None:
            login(request, user)
            return redirect('home')
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
    return redirect('home')

@login_required(login_url='/login/')
def profile_view(request):
    return render(request, 'profile.html')