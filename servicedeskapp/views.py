from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from django.http import HttpResponse
from django.contrib import messages
import json
from django.core.serializers import serialize
from django.contrib.auth.hashers import check_password,make_password
from .decorators import *
from django.core.paginator import Paginator
from datetime import datetime
from django.db.models import Max
import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

def sign_up(request):
    if request.method=='POST':
        name=request.POST.get('name')
        username=request.POST.get('username')
        email=request.POST.get('email')
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')
        if password != confirm_password:
            messages.error(request,"passwords donot match")
            return redirect('signup')
        try:
            if Sign_up.objects.filter(email=email).exists():
                messages.error(request,"Account with same email already exist")
                return redirect('signup')
            user=Sign_up.objects.create(name=name,
                username=username,email=email,
                password=password)
            user.set_password(password)
            user.save()
            messages.success(request,"Sign up successful, please login")
            return redirect('login')
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
            return redirect('signup') 
    return render(request,'signup.html')


# def login(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         password = request.POST.get('password')
#         try:
#             exist_user = Sign_up.objects.get(email=email)
#             if exist_user.check_password(password):
#                 return redirect('dashboard')
#             else:
#                 messages.error(request, "Invalid password")
#                 return redirect('login')
#         except Sign_up.DoesNotExist:
#             messages.error(request, "User with this email does not exist")
#             return redirect('login')
#     return render(request, 'login.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        try:
            exist_user = User_Management.objects.get(username=username)
            if check_password(password,exist_user.password):
                request.session['username']=exist_user.username
                request.session['role']=exist_user.role
                request.session['name']=exist_user.name
                request.session.modified=True
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid password")
                return redirect('login')
        except User_Management.DoesNotExist:
            messages.error(request, "User with this username does not exist")
            return redirect('login')
    return render(request, 'login.html')


def reset_password(request):
    if request.method=='POST':
        email=request.POST.get('email')
        new_password=request.POST.get('new_password')
        confirm_password=request.POST.get('confirm_password')
        if new_password != confirm_password:
            messages.error(request,"passwords donot match")
            return redirect('reset')
        try:
            sign=Sign_up.objects.get(email=email)

            sign.set_password(new_password)
            sign.save()
            messages.success(request, "Your password has been successfully updated. Please log in.")
            return redirect('login')
        except Sign_up.DoesNotExist:
            return redirect('reset')
    return render(request,'resetpass.html')

def logout(request):
    return redirect('login')


def dashboard(request):
    all_tickets = Create_Ticket.objects.all().order_by('-created_at')
    paginator = Paginator(all_tickets, 8) 
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    # current_date=datetime.now
    fields_to_serialize = (
        'number',
        'short_description',
        'caller',
        'priority',
        'state',
        'category',
        'assigned_to',
        'updated_at',
        'id',
        'school_name',
        'school_code',
        'assignment_group',
        'updated_by'
    )
    serialized_tickets = serialize('json', all_tickets, fields=fields_to_serialize)
    temp_list = json.loads(serialized_tickets)
    processed_tickets = []
    for item in temp_list:
        ticket_data = item['fields']
        ticket_data['id'] = item['pk'] 
        processed_tickets.append(ticket_data)
    tickets_json = json.dumps(processed_tickets)
    context = {
        # 'tickets': all_tickets, 
        # 'ticket_count': all_tickets.count(),
        # 'tickets_json': tickets_json, 
        'tickets': page_obj.object_list, 
        'ticket_count': paginator.count,
        'tickets_json': tickets_json,
        'page_obj': page_obj,
    }
    return render(request, 'dashboard.html', context)


def delete_tickets(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_tickets')
        if selected_ids:
            Create_Ticket.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f"{len(selected_ids)} ticket(s) deleted successfully.")
        else:
            messages.error(request, "No tickets selected.")
    return redirect('dashboard')


def create_ticket(request):
    if 'username' not in request.session:
        messages.error(request,"please login first")
        return redirect('login')
    ticket_count = Create_Ticket.objects.count()
    parent_incident=request.GET.get('parent_incident')
    latest_ticket = Create_Ticket.objects.aggregate(max_number=Max('number'))['max_number']     #check whats the latest number id and then give the next number.
    if latest_ticket:
        match = re.search(r'(\d+)$', latest_ticket)
        if match:                                         
            next_num = int(match.group(1)) + 1
        else:
            next_num = 10001  
    else:
        next_num = 10001 

    next_number = f'INC{next_num:07d}'
    if request.method=='POST':
        category=request.POST.get('category')
        channel=request.POST.get('channel')
        sub_category=request.POST.get('sub_category')
        state=request.POST.get('state')
        caller=request.POST.get('caller')
        caller_category=request.POST.get('caller_category')
        impact=request.POST.get('impact')
        school_name=request.POST.get('school_name')
        urgency=request.POST.get('urgency')
        school_code=request.POST.get('school_code')
        priority=request.POST.get('priority')
        assignment_group=request.POST.get('assignment_group')
        created_by=request.session.get('username')
        updated_by=request.POST.get('updated_by')
        assigned_to=request.POST.get('assigned_to')
        short_description=request.POST.get('short_description')
        description=request.POST.get('description')
        additional_comments=request.POST.get('additional_comments')
        work_notes=request.POST.get('work_notes')
        parent_incident=request.GET.get('parent_incident')
        # next_num = 10001 + ticket_count
        # number = f'INC{next_num:07d}'
        latest_ticket_number = Create_Ticket.objects.aggregate(max_number=Max('number'))['max_number']
        if latest_ticket_number:
            match = re.search(r'(\d+)$', latest_ticket_number)
            if match:
                next_num = int(match.group(1)) + 1
            else:
                next_num = 10001
        else:
            next_num = 10001
        number = f'INC{next_num:07d}'

        required_fields = {
        'School Name': school_name,
        'Caller': caller,
        'Category': category,
        'State': state,
        'Urgency': urgency,
        'Assignment Group': assignment_group,
        'Assigned To': assigned_to,
        'Short Description': short_description,
    }

        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            messages.error(request, f"The following fields are required: {', '.join(missing_fields)}")
            return render(request, 'create_ticket.html', {
                'next_number': f'INC{10001 + ticket_count:07d}',
                'selected_group': assignment_group
            })
        
        Create_Ticket.objects.create(category=category,
            channel=channel,
            sub_category=sub_category,
            state=state,
            caller=caller,
            caller_category=caller_category,
            impact=impact,
            school_name=school_name,
            urgency=urgency,
            school_code=school_code,
            priority=priority,
            assignment_group=assignment_group,
            created_by=created_by,
            updated_by=updated_by,
            assigned_to=assigned_to,
            short_description=short_description,
            description=description,
            additional_comments=additional_comments,
            work_notes=work_notes,
            number=number)
        messages.success(request,'Ticket Added')
        return redirect('dashboard')    
    else:
        selected_group=request.GET.get('assignment_group','')
        # next_num = 10001 + ticket_count                #count only the rows in the table thus identifying the next number
        # next_number = f'INC{next_num:07d}'
        group_members=[]
        if selected_group:
            try:
                group=Assignment_Group.objects.get(name=selected_group)
                group_members=Group_Members.objects.filter(group=group)
            except Assignment_Group.DoesNotExist:
                group_members=[]
        context={
            'next_number':next_number,
            'selected_group':selected_group,
            'group_members':group_members,
            'parent_incident':parent_incident,
        }
    return render(request,'create_ticket.html',context)


def update_ticket(request, ticket_id):
    if 'username' not in request.session:
        messages.error(request,"please login first")
        return redirect('login')
    single_ticket = get_object_or_404(Create_Ticket, id=ticket_id)
    selected_group = request.GET.get('assignment_group', single_ticket.assignment_group)
    if request.method == 'POST':
        old_values={
            'category': single_ticket.category,
            'channel': single_ticket.channel,
            'sub_category': single_ticket.sub_category,
            'state': single_ticket.state,
            'caller': single_ticket.caller,
            'caller_category':single_ticket.caller_category,
            'impact': single_ticket.impact,
            'school_name': single_ticket.school_name,
            'urgency': single_ticket.urgency,
            'school_code': single_ticket.school_code,
            'priority': single_ticket.priority,
            'assignment_group': single_ticket.assignment_group,
            # 'updated_by': single_ticket.updated_by,
            'assigned_to': single_ticket.assigned_to,
            'short_description': single_ticket.short_description,
            'description': single_ticket.description,
            'additional_comments': single_ticket.additional_comments,
            'work_notes': single_ticket.work_notes,
        }

        single_ticket.category = request.POST.get('category')
        single_ticket.channel = request.POST.get('channel')
        single_ticket.sub_category = request.POST.get('sub_category')
        single_ticket.state = request.POST.get('state')
        single_ticket.caller = request.POST.get('caller')
        single_ticket.caller_category = request.POST.get('caller_category')
        single_ticket.impact = request.POST.get('impact')
        single_ticket.school_name = request.POST.get('school_name')
        single_ticket.urgency = request.POST.get('urgency')
        single_ticket.school_code = request.POST.get('school_code')
        single_ticket.priority = request.POST.get('priority')
        single_ticket.assignment_group = request.POST.get('assignment_group')
        single_ticket.updated_by = request.session.get('username')
        single_ticket.assigned_to = request.POST.get('assigned_to')
        single_ticket.short_description = request.POST.get('short_description')
        single_ticket.description = request.POST.get('description')
        single_ticket.additional_comments = request.POST.get('additional_comments')
        single_ticket.work_notes = request.POST.get('work_notes')
        single_ticket.save() 

        fields_to_check=['category', 'channel', 'sub_category', 'state', 'caller','caller_category', 'impact', 
            'school_name', 'urgency', 'school_code', 'priority', 'assignment_group', 
             'assigned_to', 'short_description', 'description', 
            'additional_comments', 'work_notes']
        
        changed_fields=False
        field_changes=[]
        
        for field in fields_to_check:
            old=old_values.get(field)
            new=getattr(single_ticket,field)
            if str(old) != str(new):
                changed_fields=True
                field_changes.append({
                    'field_name':field,
                    'old_value': str(old),
                    'new_value':str(new)
                })
        if changed_fields:
            activity_record=Activity.objects.create(
                ticket=single_ticket,
                user=single_ticket.updated_by,
                action="Field changes"
            )   
            for change in field_changes:
                Field_Change.objects.create(
                    activity=activity_record,
                    field_name=change['field_name'],
                    old_value=change['old_value'],
                    new_value=change['new_value']
                )   
        messages.success(request,'Updated Successfully')
        return redirect('dashboard') 
    else:
        activities=single_ticket.activities.all().order_by('-created_at').prefetch_related('changes')
        context = {
        'tickets': single_ticket,
        'activities': activities,
        'selected_group':selected_group,
        }
    return render(request, 'update_ticket.html', context)


#GROUP LISTING, ADDING NEW GROUP, EDITING AND DELETING
def assigned_group(request):
    search=request.GET.get('q','')
    if search:
        add=Assignment_Group.objects.filter(name__icontains=search)
    else:    
        add=Assignment_Group.objects.all()
    source_page = request.GET.get('source_page')
    ticket_id = request.GET.get('ticket_id')
    context={
        'add':add,
        'source_page':source_page,
        'ticket_id':ticket_id,
    }
    return render(request,'assigned_group.html',context)

@admin_required
def new_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        group_email = request.POST.get('group_email')
        manager = request.POST.get('manager')
        parent = request.POST.get('parent')
        description = request.POST.get('description')
        group = Assignment_Group.objects.create(
            name=name, group_email=group_email, manager=manager,
            parent=parent, description=description)
        member_ids = request.POST.getlist('members') 
        for user_id in member_ids:
            if user_id.strip():
                try:
                    user_member = User_Management.objects.get(id=user_id)
                    Group_Members.objects.create(group=group, name=user_member.name)
                except User_Management.DoesNotExist:
                    pass
        if 'selected_members' in request.session:
            del request.session['selected_members']
        return redirect('assigned')
    selected_member_ids = request.session.get('selected_members', [])
    selected_members = User_Management.objects.filter(id__in=selected_member_ids)
    return render(request, 'new_group.html', {'selected_members': selected_members})

@admin_required
def edit_group(request,group_id):
    single_group=get_object_or_404(Assignment_Group,id=group_id)
    members=single_group.members.all()
    search=request.GET.get('q','')
    if search:
        members=members.filter(name__icontains=search)
    if request.method=='POST':
        single_group.name=request.POST.get('name')
        single_group.group_email=request.POST.get('group_email')
        single_group.manager=request.POST.get('manager')
        single_group.parent=request.POST.get('parent')
        single_group.description=request.POST.get('description')
        single_group.save()
        member_names=request.POST.getlist('members[]')
        submitted_members=[name.strip() for name in member_names if name.strip()]
        existing_members=list(single_group.members.values_list('name',flat=True))
        delete=set(existing_members)-set(submitted_members)
        add=set(submitted_members)-set(existing_members)
        if delete:
            Group_Members.objects.filter(group=single_group,name__in=delete).delete()
        for name in add:
            Group_Members.objects.create(group=single_group,name=name)
        messages.success(request,"Updated Successfully")
        return redirect('assigned')
    context={
        'group':single_group,
        'members':members
    }
    return render(request,'edit_group.html',context)

@admin_required
def delete_group(request,group_id):
    d_group=get_object_or_404(Assignment_Group,id=group_id)
    d_group.delete()
    return redirect('assigned')

@admin_required
def preview(request):
    return render(request,'preview_group.html')


#USER LISTING, ADDING USER, EDIT AND DELETE
@admin_required
def user_management(request):
    add=User_Management.objects.all()
    return render(request,'user_management.html',{'add':add})

@admin_required
def create_user(request):
    if request.method=='POST':
        name=request.POST.get('name')
        username=request.POST.get('username')
        email=request.POST.get('email')
        phone=request.POST.get('phone')
        role=request.POST.get('role')
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')
        if not phone.isdigit() or len(phone) != 10:
            return render(request, 'create_user.html', {'error': 'Phone number must be 10 digits.'})
        if password!=confirm_password:
            messages.error(request,"passwords don't match")
            return redirect('create_user')
        hashed_password=make_password(password)
        User_Management.objects.create(name=name,username=username,email=email,phone=phone,role=role,password=hashed_password)
        messages.success(request,"User created successfully")
        return redirect('user_management')
    return render(request,'create_user.html')

@admin_required
def edit_user(request,user_id):
    single_user=get_object_or_404(User_Management,id=user_id)
    if request.method=='POST':
        single_user.name=request.POST.get('name')
        single_user.username=request.POST.get('username')
        single_user.email=request.POST.get('email')
        single_user.phone=request.POST.get('phone')
        single_user.role=request.POST.get('role')
        password=request.POST.get('password')
        confirm_password=request.POST.get('confirm_password')
        if not single_user.phone.isdigit() or len(single_user.phone) != 10:
            return render(request, 'edit_user.html', {'error': 'Phone number must be 10 digits.'})
        if password!=confirm_password:
            messages.error(request,"passwords don't match")
            return redirect('edit_user',user_id=single_user.id)
        if password.strip() != "":
            single_user.password=make_password(password)
        single_user.save()
        messages.success(request,"updated successfully")
        return redirect('user_management')
    context={
            's_user': single_user
        }
    return render(request,'edit_user.html',context)

@admin_required
def delete_user(request,user_id):
    user=get_object_or_404(User_Management,id=user_id)
    user.delete()
    return redirect('user_management')



def parent_incident(request):
    all_tickets = Create_Ticket.objects.all().order_by('-created_at')
    fields_to_serialize = (
        'number',
        'short_description',
        'assigned_to',
        'assignment_group',
    )
    serialized_tickets = serialize('json', all_tickets, fields=fields_to_serialize)
    temp_list = json.loads(serialized_tickets)
    processed_tickets = []
    for item in temp_list:
        ticket_data = item['fields']
        ticket_data['id'] = item['pk'] 
        processed_tickets.append(ticket_data)
    tickets_json = json.dumps(processed_tickets)
    context = {
        'tickets': all_tickets, 
        'ticket_count': all_tickets.count(),
        'tickets_json': tickets_json, 
    }
    return render(request,'parent_incident.html',context)


def group_members(request):
    users=User_Management.objects.filter(role__iexact='user')    
    if request.method == 'POST':
        selected_members_ids = request.POST.getlist('members') 
        request.session['selected_members'] = selected_members_ids 
        return redirect('new_group')
    initial_member_ids = request.session.get('selected_members', [])
    available_users = users.exclude(id__in=initial_member_ids)
    selected_members = User_Management.objects.filter(id__in=initial_member_ids)
    context={
        'users': available_users,
        'initial_selected_members': selected_members 
    }
    return render(request, 'group_members.html',context)

@admin_required
def master_data(request):
    data=Master_Data.objects.all()
    context={
        'data':data
    }
    return render(request,'master_data.html',context)

@admin_required
def master_data_add(request):
    if request.method=='POST':
        name=request.POST.get('name')
        code=request.POST.get('code')
        email=request.POST.get('email')
        phone=request.POST.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            return render(request, 'master_data_add.html', {'error': 'Phone number must be 10 digits.'})
        Master_Data.objects.create(name=name,code=code,email=email,phone=phone)
        messages.success(request,'Details Added')
        return redirect('master_data')
    return render(request,'master_data_add.html')

@admin_required
def master_data_edit(request,master_id):
    single_master_data=get_object_or_404(Master_Data,id=master_id)
    if request.method=='POST':
        single_master_data.name=request.POST.get('name')
        single_master_data.code=request.POST.get('code')
        single_master_data.email=request.POST.get('email')
        single_master_data.phone=request.POST.get('phone')
        if not single_master_data.phone.isdigit() or len(single_master_data.phone) != 10:
            return render(request, 'master_data_edit.html', {'error': 'Phone number must be 10 digits.'})
        single_master_data.save()
        messages.success(request,'Updated Successfully')
        return redirect('master_data')
    context={
        'single_data':single_master_data
    }
    return render(request,'master_data_edit.html',context)

@admin_required
def master_data_delete(request,master_id):
    master=get_object_or_404(Master_Data,id=master_id)
    master.delete()
    return redirect('master_data')

@admin_required
def masterdata_overview(request):
    return render(request,'masterdata_overview.html')

@admin_required
def group_details(request):
    search=request.GET.get('q','')
    if search:
        add=Assignment_Group.objects.filter(name__icontains=search)
    else:    
        add=Assignment_Group.objects.all()
    source_page = request.GET.get('source_page')
    ticket_id = request.GET.get('ticket_id')
    context={
        'add':add,
        'source_page':source_page,
        'ticket_id':ticket_id,
    }
    return render(request,'group_details.html',context)


