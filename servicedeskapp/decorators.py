from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    def wrapper(request,*args,**kwargs):
        role=request.session.get('role')
        if role!='admin':
            messages.error(request,"Accesss denied.Admins only")
            return redirect('dashboard')
        return view_func(request,*args,**kwargs)
    return wrapper

