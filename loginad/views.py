from __future__ import unicode_literals
from django.shortcuts import render, redirect, render_to_response, get_object_or_404
from django.views import View
from django.http import HttpResponseRedirect, HttpResponse, Http404, JsonResponse
from django.views.decorators.cache import cache_control
from django.template import RequestContext, Template, Context
from uuid import uuid4
from django.db.models import Q, F
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.contrib.auth.hashers import make_password, check_password
from django.contrib import messages
from app_api.models import *
import os, shutil
from terrarium_app.common import *
from django.contrib import messages
from uuid import uuid4
import json

class AdminLogin(View):

    ''' Admin login functionality '''

    template = 'admin_template/login.html'
    
    def get(self, request):
        if request.user.is_superuser:
            return redirect('admindashboard')
        return render(request, self.template)

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']

        # Check user authentication

        user = authenticate(username= username, password= password, is_superuser= 1)
        if user is not None and user.is_superuser is True:
            if user.is_active:
                login(request, user)
                return redirect('admindashboard')
        else:
            messages.add_message(request, messages.ERROR, "Username and password is wrong.")
            return redirect('adminlogin')
class AddNewUser(View):

    ''' Admin login functionality '''

    template = 'admin_template/addnewuser.html'
    
    def get(self, request):
        if request.user.is_superuser:
            return redirect('admindashboard')
        return render(request, self.template)

    def post(self, request):
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['emailid']

        # Check user authentication
        newuser = User()
        newuser.username = username
        newuser.is_active = True
        newuser.password = make_password(password)
        newuser.email =  email
        newuser.save()

        messages.add_message(request, messages.SUCCESS, "New User Registered Successfully.")
        return redirect('newuser')

class AdminLogout(View):

    def get(self, request):

        ''' User logout action '''

        logout( request )
        return redirect('adminlogin')


class AdminForgotPassword(View):

    # Forgot Password for admin user by email

    template = 'admin_template/forgotpassword.html'


    def get(self, request):
        if request.user.is_superuser:
            return redirect('admindashboard')
        return render(request, self.template)

    def post(self, request, *args, **kwargs):
        adminforgot = User.objects.filter(email = request.POST['email'], is_superuser = 1)
        if adminforgot:
            try:
                # Replace forgot password template with new data
                numbercode = str(uuid4())[0:8]
                email_html = "Your new password is : " + numbercode

                '''' -----Email Settings----- '''
                objemail = SendMail.mail(request, "New password Request", request.POST['email'], email_html )
                '''' -----End Email setting----- '''

                if objemail:
                    adminforgot[0].password = make_password(numbercode)
                    adminforgot[0].save()
                    messages.add_message(request, messages.SUCCESS, "New password has been sent to your email address.")
                    return redirect('adminforgot')
                else:
                    messages.add_message(request, messages.ERROR, "Something went wrong.Please try again letter.")
                    return redirect('adminforgot')

            except:
                messages.add_message(request, messages.ERROR, "Something went wrong.Please try again letter.")
                return redirect('adminforgot')
        else:
            messages.add_message(request, messages.ERROR,"Email does not exist.")
            return redirect('adminforgot')


class ChangeForgotPassword(View):
    template = 'admin_template/changeforgotpassword.html'

    def get(self, request, key, *args, **kwargs):
        if request.user.is_superuser:
            return redirect('admindashboard')

        return render(request, self.template)


    def post(self, request, key, *args, **kwargs):
        if request.user.is_superuser:
            return redirect('admindashboard')
        password = request.POST['newpassword']
        decoded_data = base64.b64decode(key)
        try: 
            user = User.objects.get(email=str(decoded_data))

            user.set_password(password)
            user.save()
            messages.add_message(request, messages.SUCCESS, str(message.changeforgotpassword))
            return  redirect('adminlogin')
        except:
            messages.add_message(request, messages.ERROR, str(message.forgotinvalidlink))
            return HttpResponseRedirect(str(request.path))


class AdminChangePassword(View):
    templatchangepassword = 'admin_template/changepassword.html'
    
    @cache_control(no_cache=True, must_revalidate=True, no_store=True)
    def get(self, request):
        if not request.user.is_superuser:
            return redirect('adminlogin')
        return render(request, self.templatchangepassword)

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return redirect('adminlogin')

        changepwd =  User.objects.get(id= request.user.id)

        oldpassword = request.POST['oldpassword']
        newpassword = request.POST['newpassword']
        passwordString = changepwd.password
        checkPassword = check_password(oldpassword, passwordString)
        if checkPassword :
            makenewpassword = make_password(newpassword)
            changepwd.password = makenewpassword 
            changepwd.save()
            update_session_auth_hash(request, changepwd) 
            messages.add_message( request, messages.SUCCESS,  "Your password has been changed.")
            return HttpResponseRedirect(str(request.path))
        else:
            messages.add_message( request, messages.ERROR, "Your old password is wrong.")
            return HttpResponseRedirect(str(request.path))


class UpdateAdminProfile(View):
    template = 'admin_template/adminupdateprofile.html'
    imageheight =100
    imagewidth =100

    @cache_control(no_cache=True, must_revalidate=True, no_store=True)
    def get(self, request):
        if not request.user.is_superuser:
            return redirect('adminlogin')
        return render(request, self.template)

    def post(self, request):
        if not request.user.is_superuser:
            return redirect('adminlogin')

        adminprofile =  User.objects.get(id= request.user.id)
        adminprofile.email = request.POST['email']
        adminprofile.mobilenumber = request.POST['phone']
        adminprofile.first_name = request.POST['firstname']
        adminprofile.username = request.POST['username']
        adminprofile.last_name = request.POST['lastname']
        adminprofile.address = request.POST['address']
        if 'profileimg' in request.FILES:

            ''' crop image '''
            timepath ='userimage/user_{0}/{1}/'.format(request.user.id, datetime.now().strftime( '%d-%m-%Y %H:%M:%S' ))
            if os.path.exists(settings.MEDIA_URL+ 'userimage/user_{0}/'.format(request.user.id)):
                shutil.rmtree(settings.MEDIA_URL + 'userimage/user_{0}/'.format(request.user.id))

            adminprofile.profile_pic1 = timepath + str(request.FILES['profileimg'])
            CropImage.saveimage(request.FILES['profileimg'],timepath, self.imageheight, self.imagewidth)
            ''' End crop '''

        adminprofile.save()
        messages.add_message(request, messages.SUCCESS, "Profile update successfully.")
        return redirect('updateadminprofile')


class AdminDashBoard(View):
    template = 'admin_template/dashboard.html'

    @cache_control(no_cache=True, must_revalidate=True, no_store=True)
    def get(self, request):
        if not request.user.is_superuser:
            return redirect('adminlogin')
        return render(request, self.template)


class CheckEmailExists(View):

    def get(self, request):
        try:
            User.objects.get(email=request.GET['emailid'])
            reponse = json.dumps("Email already in use!")
            return HttpResponse(reponse)
        except Exception as e:
            reponse = json.dumps(True)
            return HttpResponse(reponse)


class CheckUserNameExists(View):

    def get(self, request):
        try:
            User.objects.get(username=request.GET['username'])
            reponse = json.dumps("User name already in use!")
            return HttpResponse(reponse)
        except Exception as e:
            reponse = json.dumps(True)
            return HttpResponse(reponse)


class CheckEditEmailExists(View):

    def get(self, request):
        # Check userid and email same
        check = User.objects.filter(email=request.GET['emailid'], id  = request.GET['userid'])
        if check.exists():
            reponse = json.dumps(True)
            return HttpResponse(reponse)
        else:
            # email exist check
            check = User.objects.filter(email=request.GET['emailid'])
            if check.exists():
                reponse = json.dumps("Email already in use!")
                return HttpResponse(reponse)
            else:
                reponse = json.dumps(True)
                return HttpResponse(reponse)