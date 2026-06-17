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

def admin_dashboard(request):
    return render(request, 'admin_dashboard.html')

def admin_requests(request):
    return render(request, 'admin_requests.html')

def admin_blog(request):
    return render(request, 'admin_blog.html')

def admin_gallery(request):
    return render(request, 'admin_gallery.html')
