from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def profile(request):
    return render(request, 'profile.html')

def items(request):
    return render(request, 'items.html')

def feedback(request):
    return render(request, 'feedback.html')

def blog(request):
    return render(request, 'blog.html')

def admin_page(request):
    return render(request, 'admin.html')
