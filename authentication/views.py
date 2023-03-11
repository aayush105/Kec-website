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
from .models import FetchedData,Subscriber
from django.core.paginator import Paginator
from django.utils.html import strip_tags




# Create your views here.
def home(request):
    return render(request,"home/index.html")

def checkSymbol(request):
    return HttpResponse(request,"<h1>done</h1>")


def subscribe(request):
    if request.method == 'POST':
        fullname = request.POST['fullname']
        email = request.POST['email']
        bs_year = request.POST['bs_year']
        faculty = request.POST['faculty']
        year = request.POST['year']
        # check if the email is already subscribed
        if Subscriber.objects.filter(email=email).exists():
            return render(request, 'authentication/already_subscribed.html')
        # create a new subscriber object
        subscriber = Subscriber(fullname=fullname,email=email, bs_year=bs_year, faculty=faculty, year=year)
        subscriber.save()
        # send activation email
        current_site = get_current_site(request)
        subject = 'Activate your subscription'
        message = render_to_string('authentication/activation_email.html', {
            'user': subscriber,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(subscriber.pk)),
            'token': generate_token.make_token(subscriber),
        })
        html_message = render_to_string('authentication/activation_email.html', {
            'user': subscriber,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(subscriber.pk)),
            'token': generate_token.make_token(subscriber),
        })
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, strip_tags(message), from_email, recipient_list, html_message=html_message)
        return render(request, 'authentication/activation_sent.html')
    return render(request, 'home/subscribe.html')

def notices(request):
    fetched_data = FetchedData.objects.all()
    paginator = Paginator(fetched_data, 10)
    page = request.GET.get('page')
    fetched_data = paginator.get_page(page)
    context = {'fetched_data': fetched_data}
    return render(request,'home/notices.html',context)



def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        subscriber = Subscriber.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, Subscriber.DoesNotExist):
        subscriber = None

    if subscriber is not None and generate_token.check_token(subscriber, token):
        subscriber.is_active = True
        subscriber.save()
        messages.success(request, "Activation Successful.")
        return redirect("home")
    else:
        return render(request, 'authentication/activation_failed.html')
