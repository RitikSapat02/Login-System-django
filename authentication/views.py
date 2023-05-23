from email.message import EmailMessage
from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate,login,logout
from login_project import settings
from django.core.mail import send_mail,EmailMessage
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tokens import generate_token

# Create your views here.
def home(request):
    return render(request,'index.html')

def signup(request):
    #fetch data if posted any data
    if request.method=='POST':
        username = request.POST.get('username')
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        #validations
        if User.objects.filter(username=username):
            messages.error(request,'Username already exist!')
            return redirect('home')
        
        if User.objects.filter(email=email):
            messages.error(request,'Email already registered !')
            return redirect('home')
        
        if len(username)>10:
            messages.error(request,'Username must be less than 100 characters')
            return redirect('home')
        
        if password != cpassword:
            messages.error(request,"Passwords didn't matched")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request,'Username must be Alpha-Numeric')
            return redirect('home')
        
        myuser = User.objects.create_user(username,email,password)

        myuser.first_name=fname
        myuser.last_name=lname
        myuser.is_active = False   #after confirming email only it will active
        myuser.save()

        messages.success(request,"Your Account has been successfully created. We have sent you a cofirmation email , please confirmyour email in order to activate account")

        # welcome Email

        subject="Welcome to our very own Login-System!!"
        message = f"Hello {myuser.first_name}\nWelcome to our login-system!!\nThank you for visiting our website \nWe have also sent you a confirmation email,please confirm your emial address in order to activate your account.\n\nThanking you\n Ritik Sapat"

        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject,message,from_email,to_list,fail_silently=True)

        #Email Address Confirmation Email

        current_site = get_current_site(request)   #To get domain like local server or other domain of current site
        email_subject = 'Confirm your email #Login-system - Django Login!'
        message2 =render_to_string('email_confirmation.html',{
            'name':myuser.first_name,
            'domain':current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(myuser.pk)),
            'token':generate_token.make_token(myuser),
        })

        email = EmailMessage(
            email_subject,
            message2,
            settings.EMAIL_HOST_USER,
            [myuser.email],
        )

        email.fail_silently = True
        email.send()

        return redirect('signin')
    return render(request,"signup.html")

def signin(request):

    if request.method == 'POST':
        username = request.POST['username'] 
        password = request.POST['password'] 
       
        user = authenticate(username=username,password=password)

        if user is not None:
            login(request,user)
            fname = user.first_name
            # lname = user.last_name
            return render(request,'index.html',{'fname':fname})
        else:
            messages.error(request,"Bad credentials!!")
            return redirect('home')
        
    return render(request,'signin.html')

def signout(request):
    logout(request)
    messages.success(request,"logged out successfully!")
    return redirect('home')

def activate(request,uidb64,token):
    try:
        uid=force_str(urlsafe_base64_decode(uidb64))
        myuser = User.objects.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        myuser = None
    
    if myuser is not None and generate_token.check_token(myuser,token):
        myuser.is_active = True
        myuser.save()
        login(request,myuser)
        messages.success(request,"Your Account has been activated!!")
        return redirect('signin')
    else:
        return render(request,'activation_failed.html')