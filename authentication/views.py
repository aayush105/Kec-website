from authentication.utils import TeamMember
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
from .models import FetchedData,Subscriber,ResultData
from django.core.paginator import Paginator
from django.utils.html import strip_tags



# Create your views here.
def home(request):
    return render(request,"home/index.html")

def checkSymbol(request):
    
    bs = request.POST["bs_year"]
    symbol = request.POST["symbol_no"]
    faculty = request.POST["faculty"]
    faculty_year = request.POST["faculty_year"]
    faculty_part = request.POST["faculty_part"]
    
    if ResultData.objects.filter(faculty=faculty,bs=bs,year=faculty_year,part=faculty_part,symbol=symbol).exists():
        messages.success(request,"Congratulations! The symbol no has passed the exam.")
    else:
        messages.warning(request,"Sorry! The symbol no has not passed.")

    return render(request,"home/index.html",context={"messages":messages.get_messages(request),"page":"index"})


def subscribe(request):
    if request.method == 'POST':
        fullname = request.POST['fullname']
        email = request.POST['email']
        # bs_year = request.POST['bs_year']
        bs_year = 2079
        faculty = request.POST['faculty']
        year = request.POST['year']
        part = request.POST["faculty_part"]
        symbol = request.POST['symbol_no']
        # check if the email is already subscribed
        if Subscriber.objects.filter(email=email).exists():
            return render(request, 'authentication/already_subscribed.html')
        # create a new subscriber object
        subscriber = Subscriber(fullname=fullname,email=email, bs_year=bs_year, faculty=faculty, year=year,part=part,symbol=symbol)
        subscriber.save()
        # send activation email
        current_site = get_current_site(request)
        subject = 'Activate your subscription'
        message = render_to_string('authentication/email_confirmation.html', {
            'name': subscriber,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(subscriber.pk)),
            'token': generate_token.make_token(subscriber),
        })
        html_message = render_to_string('authentication/email_confirmation.html', {
            'name': subscriber,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(subscriber.pk)),
            'token': generate_token.make_token(subscriber),
        })
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [email]
        send_mail(subject, strip_tags(message), from_email, recipient_list, html_message=html_message)
        return render(request,"authentication/activation_sent.html")
    return render(request, 'home/subscribe.html')

def notices(request):
    fetched_data = FetchedData.objects.all()
    paginator = Paginator(fetched_data, 10)
    page = request.GET.get('page')
    fetched_data = paginator.get_page(page)
    context = {'fetched_data': fetched_data}
    return render(request,'home/notices.html',context)

def about(request):
    members = [
        TeamMember(
            name='Aayush Shrestha',
            title='CEO',
            bio='Lorem ipsum dolor sit amet, consectetur adipiscing elit. Duis dapibus ex mauris, sed lobortis velit efficitur id. Pellentesque sit amet leo non orci pharetra commodo eu a nisl.',
            profile_image='https://www.jokesforfunny.com/wp-content/uploads/2021/06/0596bdb89b60fe771acd2f5972a9d3e3.jpg',
            github="https://github.com/ayushrestha105",
            email="kan077bct004@kec.edu.np",
            phone="9814596362"
        ),
        TeamMember(
            name='Ankit Kafle',
            title='COO',
            bio='Ut imperdiet nunc et justo fringilla ultrices. In semper diam quis commodo commodo. Suspendisse potenti. Nullam aliquam iaculis tortor, in varius justo finibus vel. ',
            profile_image='https://nextluxury.com/wp-content/uploads/funny-profile-pictures-7.jpg',
        ),
       
    ]
    
    context = {
        'team_members': members,
    }

    return render(request, 'home/about.html', context)

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        # validate form data
        if not name or not email or not subject or not message:
            messages.error(request, 'Please fill in all fields.')
            return redirect('contact')

        # send email
        send_mail(
            subject=subject,
            message=f'From: {name} <{email}>\n\n{message}',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[settings.CONTACT_EMAIL],
            fail_silently=False,
        )

        messages.success(request, 'Your message has been sent. Thank you!')
        return redirect('contact')

    return render(request, 'home/contact.html')


def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        subscriber = Subscriber.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, Subscriber.DoesNotExist):
        subscriber = None

    if subscriber is not None and generate_token.check_token(subscriber, token):
        subscriber.is_active = True
        subscriber.save()
        return render(request,"authentication/subscription_success.html")
    else:
        return render(request, 'authentication/activation_failed.html')
