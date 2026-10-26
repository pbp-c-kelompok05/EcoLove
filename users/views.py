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
            return redirect('items:show_marketplace')
        else:
            messages.error(request, "Invalid username or password.")   

    return render(request, 'login.html', {'username': username_input})

def register_user(request):
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        email_input = request.POST.get('email', '').strip()
        password_input = request.POST.get('password', '')

        # Pass inputs back to template context if validation fails
        context = {
            'username': username_input,
            'email': email_input,
        }
        
        # 1. Check apa usn sudah ada
        if User.objects.filter(username=username_input).exists():
            messages.error(request, "Username is already taken.")
            return render(request, 'register.html', context)

        # 2. Validasi Password
        if len(password_input) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'register.html', context)
        
        if not any(char.isupper() for char in password_input):
            messages.error(request, "Password must contain at least 1 uppercase letter (A-Z).")
            return render(request, 'register.html', context)
        
        if not any(not char.isalpha() for char in password_input):
            messages.error(request, "Password must contain at least 1 number or unique character (e.g., . , ! @ 1 2).")
            return render(request, 'register.html', context)

        # 3. Buat akun bila terpenuhi
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
    return render(request, 'profile.html')