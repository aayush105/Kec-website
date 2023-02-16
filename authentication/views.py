from base64 import urlsafe_b64encode
from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from kecWebsite import settings
from django.core.mail import send_mail, EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from . tokens import generate_token

# Create your views here.
def home(request):
    return render(request,"home/index.html")

def signup(request):
    
    if request.method == "POST":
        fullname = request.POST.get('fullname')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = User.objects.create_user(username=username, email=email,password=password)
        user.is_active = False
        user.save()

        current_site = get_current_site(request)
       
        email_subject = "Confirm your email @ KEC Website"
        message2 = render_to_string("email_confirmation.html",{
            'user': user,
            'domain' : current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': generate_token.make_token(user),
        })
        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [user.email]
        )
        email.fail_silently = True
        email.send()


        messages.success(request,"Your account has been successfuly created. We have sent you a confirmation email, please confirm your email in order to activate your account.")
        return redirect('signin')
    else:
        return render(request,'authentication/signup.html')

def signin(request):
    
    if request.method== "POST":
        username=request.POST.get('username')
        email=request.POST.get('email')
        password=request.POST.get('password')

        user=authenticate(username=username,password=password)  

        if user is not None:
            login(request,user)
            # fullname=user.fullname
            fullname=user.username
            return render(request,"home/result.html",{'fullname':fullname})
            
        else:
            messages.error(request, "Bad credentials!")
            return redirect('signin')
    
    return render(request,"authentication/signin.html")

def signout(request):
    pass
    logout(request)
    # messages.success(request,"Logged Out Successfully!")
    return redirect('home')

def result(request):
    return render(request,"home/result.html")


def activate(request,uidb64,token):
    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        myuser= User.objects.get(pk=uid)
    
    except (TypeError,ValueError,OverflowError, User.DoesNotExist):
        myuser=None
        
    if myuser is not None and generate_token.check_token(myuser, token):
        myuser.is_active=True
        myuser.save()
        login(request,myuser)
        return redirect('signin')
    else:
        return render(request, 'activation_failed.html')

