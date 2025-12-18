from django.shortcuts import render,redirect,get_object_or_404
from .models import *
from django.http import HttpResponse
from django.contrib import messages
import json
from django.core.serializers import serialize
from django.contrib.auth.hashers import check_password,make_password
from .decorators import *
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datetime import datetime
from django.db.models import Max
import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.utils.timezone import localtime
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.http import urlsafe_base64_decode
from django.db.models import Max
from django.db import transaction
from datetime import timedelta
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils.safestring import mark_safe


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
                return redirect('overview')
            else:
                messages.error(request, "Invalid password")
                return redirect('login')
        except User_Management.DoesNotExist:
            messages.error(request, "User with this username does not exist")
            return redirect('login')
    return render(request, 'login.html')



token_generator = PasswordResetTokenGenerator()

def reset_password(request):
    if request.method == "POST":
        email = request.POST.get("email")

        try:
            user = User_Management.objects.get(email=email)
        except User_Management.DoesNotExist:
            messages.error(request, "Email not found.")
            return redirect("reset")
        uidb64 = urlsafe_base64_encode(force_bytes(user.id))
        token = token_generator.make_token(user)
        reset_url = request.build_absolute_uri(
            reverse("reset_confirm", kwargs={"uidb64": uidb64, "token": token})
        )
        send_mail(
            subject="Password Reset Instructions",
            message=f"Click the link below to reset your password (valid for 10 minutes):\n{reset_url}",
            from_email="your-email@gmail.com",
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request, "Reset link sent! Check your email.")
        return redirect("login")
    return render(request, "resetpass.html")


def reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User_Management.objects.get(pk=uid)
    except:
        user = None
    if user is None or not token_generator.check_token(user, token):
        return HttpResponse("Reset link is invalid or has expired.")
    if request.method == "POST":
        new_pass = request.POST.get("new_password")
        confirm_pass = request.POST.get("confirm_password")
        if new_pass != confirm_pass:
            messages.error(request, "Passwords do not match.")
            return redirect(request.path)
        user.set_password(new_pass)
        user.save()
        messages.success(request, "Password reset successful. Login now.")
        return redirect("login")
    return render(request, "reset_confirm.html")

def logout(request):
    request.session.flush()
    return redirect('login')


from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def parent_caller(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email', '')

        if not name or not phone:
            return JsonResponse({'success': False, 'error': 'Name and phone required'})

        caller, created = Master_Data.objects.update_or_create(
            phone=phone,
            defaults={
                'name': name,
                'email': email,
                'role': 'parent' 
            }
        )
        return JsonResponse({
            'success': True,
            'caller_name': caller.name
        })

    return JsonResponse({'success': False, 'error': 'Invalid request'})



def dashboard(request):
    filter_type = request.GET.get('filter')
    all_tickets = Create_Ticket.objects.all().order_by('-created_at')
    if filter_type == 'resolved':
        all_tickets = all_tickets.filter(state='resolved')
    
    for ticket in all_tickets: 
        caller=Caller_Details.objects.filter(caller_name=ticket.caller).first()
        ticket.caller_email = ticket.caller_details.caller_email if ticket.caller_details else None

        if ticket.priority and ticket.priority.time and ticket.priority.unit:
            sla_minutes = ticket.priority.time
            if ticket.priority.unit == 'hours':
                sla_minutes *= 60
            elif ticket.priority.unit == 'days':
                sla_minutes *= 1440  # 24*60
            
            deadline = ticket.created_at + timedelta(minutes=sla_minutes)
            remaining = deadline - timezone.now()
            
            if remaining.total_seconds() > 0:
                total_hours_left = remaining.total_seconds() / 3600

                if total_hours_left > 48:          # More than 2 days
                    ticket.time_left_badge_class = "safe"
                elif total_hours_left > 24:         # 1–2 days
                    ticket.time_left_badge_class = "approaching"
                elif total_hours_left > 4:          # 4–24 hours
                    ticket.time_left_badge_class = "warning"
                else:                               # Less than 4 hours
                    ticket.time_left_badge_class = "urgent"
                
                # Format the display text nicely
                days = remaining.days
                hours = int(remaining.total_seconds() / 3600) % 24
                minutes = int(remaining.total_seconds() / 60) % 60
                
                if days > 0:
                    ticket.time_left = f"{days}d {hours}h"
                elif hours > 0:
                    ticket.time_left = f"{hours}h {minutes}m"
                else:
                    ticket.time_left = f"{minutes}m"
            else:
                ticket.time_left = "Overdue"
                ticket.time_left_badge_class = "overdue"
        else:
            ticket.time_left = "No SLA"
            ticket.time_left_badge_class = "nosla"

    paginator = Paginator(all_tickets, 8)
    page_number = request.GET.get('page')
    try:
        page_obj = paginator.page(page_number)
    except (PageNotAnInteger, EmptyPage):

        page_obj = paginator.page(1)

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
        'tickets': page_obj.object_list, 
        'ticket_count': paginator.count,
        'tickets_json': tickets_json,
        'page_obj': page_obj,
        'current_username': request.session.get('username'),      
        'current_user_fullname': request.session.get('name', request.session.get('username')),
        'current_filter': filter_type,
    }
    return render(request, 'tickets/dashboard.html', context)

def create_ticket(request):
    if 'username' not in request.session:
        messages.error(request, "Please login first")
        return redirect('login')

    priorities = Priority_Data.objects.all()
    ticket_count = Create_Ticket.objects.count()
    latest_ticket = Create_Ticket.objects.aggregate(max_number=Max('number'))['max_number']
    if latest_ticket:
        match = re.search(r'(\d+)$', latest_ticket)
        if match:
            next_num = int(match.group(1)) + 1
        else:
            next_num = 10001
    else:
        next_num = 10001
    next_number = f'INC{next_num:07d}'
    
    group_members = []
    parent_caller = request.GET.get('caller', '')
    
    if request.method == 'POST':
        category = request.POST.get('category')
        channel = request.POST.get('channel')
        modules = request.POST.get('modules')
        state = request.POST.get('state')
        caller_name = request.POST.get('caller') 
        platform = request.POST.get('platform')
        impact = request.POST.get('impact')
        school_name = request.POST.get('school_name')
        school_code = request.POST.get('school_code')
        urgency = request.POST.get('urgency')
        priority_id = request.POST.get('priority')
        priority_obj = Priority_Data.objects.get(id=priority_id) if priority_id else None
        assignment_group = request.POST.get('assignment_group')
        created_by = request.session.get('username')
        updated_by = request.POST.get('updated_by')
        assigned_to = request.POST.get('assigned_to')
        short_description = request.POST.get('short_description')
        description = request.POST.get('description')
        additional_comments = request.POST.get('additional_comments')
        work_notes = request.POST.get('work_notes')
        parent_incident = request.POST.get('parent_incident')
        problem = request.POST.get('problem')
        changed_request = request.POST.get('change_request')
        caused_by_change = request.POST.get('caused_by_change')

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
            'Caller': caller_name,
            'Category': category,
            'State': state,
            'Urgency': urgency,
            'Assignment Group': assignment_group,
            'Short Description': short_description,
        }
        
        missing_fields = [field for field, value in required_fields.items() if not value]
        if missing_fields:
            messages.error(request, f"The following fields are required: {', '.join(missing_fields)}")
            selected_group = request.POST.get('assignment_group', '')
            return render(request, 'tickets/create_ticket.html', {
                'next_number': next_number,
                'selected_group': selected_group,
                'group_members': group_members,
                'parent_caller': parent_caller,
                'latest_caller': request.session.get('last_caller_name', ''),
                'latest_school_name': school_name,  
                'latest_school_code': school_code,
                'priorities': priorities,
            })

        caller=Caller_Details.objects.filter(caller_name=caller_name)
        if caller.exists():
            caller = caller.first()
            caller_email = caller.caller_email
        else:
            messages.error(request, "Caller not found.")
            return render(request, 'tickets/create_ticket.html', {
                'next_number': next_number,
                'selected_group': assignment_group,
                'group_members': group_members,
                'parent_caller': parent_caller,
                'latest_caller': request.session.get('last_caller_name', ''),
                'priorities': priorities,

            })

        caller_details_obj = None
        if caller_name:
            caller = Caller_Details.objects.filter(caller_name=caller_name)
        if caller.exists():
            caller_details_obj = caller.first()  # ✅ Single instance
        else:
            caller_details_obj = Caller_Details.objects.create(
                caller_name=caller_name,
                school_name=school_name,
                school_code=school_code
            )
            messages.info(request, f"New caller '{caller_name}' created automatically.")
        
        # Create ticket with transaction for data integrity
        with transaction.atomic():
            ticket = Create_Ticket.objects.create(
                category=category,
                channel=channel,
                modules=modules,
                state=state,
                caller=caller_name,  # Display name
                caller_details=caller_details_obj,  # ForeignKey relationship
                platform=platform,
                impact=impact,
                school_name=school_name,
                school_code=school_code,
                urgency=urgency,
                priority=priority_obj,
                assignment_group=assignment_group,
                created_by=created_by,
                updated_by=updated_by,
                assigned_to=assigned_to,
                short_description=short_description,
                description=description,
                additional_comments=additional_comments,
                work_notes=work_notes,
                number=number,
                parent_incident=parent_incident,
                problem=problem,
                change_request=changed_request,
                caused_by_change=caused_by_change,
            )

            Ticket_Duration.objects.create(
                ticket=ticket,ticket_number=ticket.number,
                category=ticket.category,modules=ticket.modules,opened_time=ticket.created_at,
            )
            

        # Send email notification
        if caller_details_obj and caller_details_obj.caller_email:
            caller_email = caller_details_obj.caller_email
            subject = f"New Ticket Created: {number}"
            message = (
                f"Dear {caller_name},\n\n"
                f"A new ticket has been created for your school {school_name}.\n\n"
                f"Ticket Number: {number}\n"
                f"Short Description: {short_description}\n"
                f"Additional Comments: {additional_comments}\n\n"
                f"Our team is actively looking into the issue and will keep you updated.\n"
                f"If you need any further assistance, kindly reach out to our support team.\n\n"
                f"Regards,\n"
                f"IT Support Team\n"
                f"Edship Technologies"
            )
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [caller_email]
            try:
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)
            except Exception as e:
                messages.warning(request, f'Ticket created but email failed: {str(e)}')
        else:
            messages.success(request, f'Ticket {number} created (no caller email available).')

        for key in ['last_caller_name', 'last_caller_id', 'last_school_name', 'last_school_code']:
            request.session.pop(key, None)
        request.session.modified = True
        
        messages.success(request, f'Ticket {number} created and notification sent successfully.')
        return redirect('dashboard')
    else:
        selected_group = request.GET.get('assignment_group', '')
        if selected_group:
            try:
                group = Assignment_Group.objects.get(name=selected_group)
                group_members = Group_Members.objects.filter(group=group)
            except Assignment_Group.DoesNotExist:
                group_members = []  
           
    latest_caller = request.session.get('last_caller_name', '')
    latest_school_name = request.session.get('last_school_name', '')
    latest_school_code = request.session.get('last_school_code', '')

    context = {
        'next_number': next_number,
        'selected_group': selected_group,
        'group_members': group_members,
        'parent_caller': parent_caller,
        'latest_caller': latest_caller,
        'latest_school_name': latest_school_name,
        'latest_school_code': latest_school_code,
        'priorities': priorities,
    }
 
    return render(request, 'tickets/create_ticket.html', context)

def update_ticket(request, ticket_id):
    if 'username' not in request.session:
        messages.error(request,"please login first")
        return redirect('login')
    priorities = Priority_Data.objects.all()
    single_ticket = get_object_or_404(Create_Ticket, id=ticket_id)
    selected_group_param = request.GET.get('assignment_group')  
    current_group = single_ticket.assignment_group 
    selected_group = selected_group_param if selected_group_param else current_group
    group_members = []
    if selected_group and selected_group.strip():
        try:
            group = Assignment_Group.objects.get(name=selected_group)
            group_members = Group_Members.objects.filter(group=group).select_related('user')
        except Assignment_Group.DoesNotExist:
            group_members = []
    if request.method == 'POST':
        old_state = single_ticket.state
        old_values={
            'category': single_ticket.category,
            'channel': single_ticket.channel,
            'modules': single_ticket.modules,
            'state': single_ticket.state,
            'caller': single_ticket.caller,
            'platform': single_ticket.platform,
            'impact': single_ticket.impact,
            'school_name': single_ticket.school_name,
            'urgency': single_ticket.urgency,
            'school_code': single_ticket.school_code,
            'priority': single_ticket.priority,
            'assignment_group': single_ticket.assignment_group,
            'assigned_to': single_ticket.assigned_to,
            'short_description': single_ticket.short_description,
            'description': single_ticket.description,
            'additional_comments': single_ticket.additional_comments,
            'work_notes': single_ticket.work_notes,
            'parent_incident': single_ticket.parent_incident,
            'problem': single_ticket.problem,
            'change_request': single_ticket.change_request,
            'caused_by_change': single_ticket.caused_by_change,
        }

        single_ticket.category = request.POST.get('category')
        single_ticket.channel = request.POST.get('channel')
        single_ticket.modules = request.POST.get('modules')

        action = request.POST.get('action')
        if action == "resolve":
            resolution_code = request.POST.get('resolution_code')
            resolution_notes = request.POST.get('resolution_notes')

            if not resolution_code or not resolution_notes:
                messages.error(
                    request,
                    "Resolution Code and Resolution Notes are mandatory to resolve the ticket."
                )
                return redirect('update', ticket_id=single_ticket.id)

            single_ticket.state = "resolved"
            single_ticket.resolved_by = request.session.get('username')
            single_ticket.resolution_code = resolution_code
            single_ticket.resolution_notes = resolution_notes
            single_ticket.resolved_at = timezone.now()
        else:
            single_ticket.state = request.POST.get('state')

        single_ticket.caller = request.POST.get('caller')
        single_ticket.platform = request.POST.get('platform')
        single_ticket.impact = request.POST.get('impact')
        single_ticket.school_name = request.POST.get('school_name')
        single_ticket.urgency = request.POST.get('urgency')
        single_ticket.school_code = request.POST.get('school_code')
        priority_id = request.POST.get('priority')
        if priority_id:
            single_ticket.priority = Priority_Data.objects.get(id=priority_id)

        single_ticket.assignment_group = request.POST.get('assignment_group')
        single_ticket.updated_by = request.session.get('username')
        single_ticket.assigned_to = request.POST.get('assigned_to')
        single_ticket.short_description = request.POST.get('short_description')
        single_ticket.description = request.POST.get('description')
        single_ticket.additional_comments = request.POST.get('additional_comments')
        single_ticket.work_notes = request.POST.get('work_notes')
        single_ticket.parent_incident = request.POST.get('parent_incident')
        single_ticket.problem = request.POST.get('problem')
        single_ticket.change_request = request.POST.get('change_request')
        single_ticket.caused_by_change = request.POST.get('caused_by_change')
        single_ticket.save() 

        fields_to_check=['category', 'channel', 'modules', 'state', 'caller','platform', 'impact', 
            'school_name', 'urgency', 'school_code', 'priority', 'assignment_group', 
             'assigned_to', 'short_description', 'description', 
            'additional_comments', 'work_notes','parent_incident','problem','change_request','caused_by_change',
            'resolved_by','resolution_code','resolved_at','resolution_notes']
        
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
        # if action == "resolve":
        #     single_ticket.resolved_date = timezone.now()
        #     single_ticket.save()
        #     resolved_minute=single_ticket.resolved_date.minute
        #     resolved_hour=single_ticket.resolved_date.hour
        #     resolved_hour_to_minutes=resolved_hour*60
        #     resolved_total_minutes=resolved_hour_to_minutes+resolved_minute

        #     created_minute=single_ticket.created_at.minute
        #     created_hour=single_ticket.created_at.hour
        #     created_hour_to_minutes=created_hour*60
        #     created_total_minutes=created_hour_to_minutes+created_minute

        #     duration= resolved_total_minutes - created_total_minutes
        #     if resolved_total_minutes or created_total_minutes >= 60:
        #         hours=duration//60
        #         minutes=duration%60
        #         total_duration=f"{hours} hours {minutes} minutes"
        #     else:
        #         total_duration=f"{duration} minutes"
        #     Ticket_Duration.objects.filter(ticket=single_ticket).update(
        #         resolved_time=single_ticket.resolved_date,
        #         duration=duration,  
        #     )
        if action == "resolve":
            single_ticket.state = "resolved"
            single_ticket.resolved_by = request.session.get('username')
            single_ticket.resolved_date = timezone.now()
            single_ticket.save()

            # ✅ CORRECT duration calculation
            duration_value = single_ticket.resolved_date - single_ticket.created_at

            # ✅ Update Ticket_Duration properly
            Ticket_Duration.objects.update_or_create(
                ticket=single_ticket,
                defaults={
                    'ticket_number': single_ticket.number,
                    'category': single_ticket.category,
                    'opened_time': single_ticket.created_at,
                    'resolved_time': single_ticket.resolved_date,
                    'duration': duration_value
                }
            )
                      
            caller = (Caller_Details.objects.filter(caller_name=single_ticket.caller).order_by('-id').first())

            if caller:
                single_ticket.caller_email = caller.caller_email
            else:
                single_ticket.caller_email = None


            if single_ticket.caller_email:
                subject = f"Your ticket {single_ticket.number} has been resolved"
                message = (
                    f"Dear { caller.caller_name },\n\n"
                    f"We are happy to inform you that your reported issue has been successfully resolved.\n\n"
                    f"Ticket No.: {single_ticket.number}\n"
                    f"Short Description: {single_ticket.short_description}\n"
                    f"Additional Comments: {single_ticket.additional_comments}\n\n"
                    "If the issue reoccurs or you need further assistance, kindly inform us.\n\n"
                    "Regards,\n"
                    "IT Support Team\n"
                    "Edship Technologies\n"
                )

                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [single_ticket.caller_email])
            messages.success(request, "Ticket resolved and email notification sent.")
        else:
            messages.success(request, "Ticket updated successfully.")
        return redirect('update', ticket_id=single_ticket.id) 

    else:
        activities=single_ticket.activities.all().order_by('-created_at').prefetch_related('changes')
        context = {
        'tickets': single_ticket,
        'activities': activities,
        'selected_group':selected_group,
        'group_members': group_members,
        'priorities': priorities,

        }
    return render(request, 'tickets/update_ticket.html', context)


def delete_tickets(request):
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_tickets')
        if selected_ids:
            Create_Ticket.objects.filter(id__in=selected_ids).delete()
            messages.success(request, f"{len(selected_ids)} ticket(s) deleted successfully.")
        else:
            messages.error(request, "No tickets selected.")
    return redirect('dashboard')


#--------------------GROUP LISTING, ADDING NEW GROUP, EDITING AND DELETING---------------------------------

def assigned_group(request):
    add=Assignment_Group.objects.all()
    source_page = request.GET.get('source_page')
    ticket_id = request.GET.get('ticket_id')
    context={
        'add':add,
        'source_page':source_page,
        'ticket_id':ticket_id,
    }
    return render(request,'tickets/assigned_group.html',context)

@admin_required
def new_group(request):
    saved_form=request.session.get('group_form',{})
    if request.method == 'POST':
        if 'new_member' in request.POST:
            request.session['group_form']={
                'name': request.POST.get('name', ''),
                'group_email': request.POST.get('group_email', ''),
                'manager': request.POST.get('manager', ''),
                'parent': request.POST.get('parent', ''),
                'description': request.POST.get('description', ''),
            }
            return redirect('group_members')
        if 'create_group' in request.POST:
            name = request.POST.get('name')
            group_email = request.POST.get('group_email')
            manager = request.POST.get('manager')
            parent = request.POST.get('parent')
            description = request.POST.get('description')
            group = Assignment_Group.objects.create(
                name=name, group_email=group_email,
                manager=manager, parent=parent,
                description=description
            )
            member_ids = request.POST.getlist('members')
            for user_id in member_ids:
                if user_id:
                    user = User_Management.objects.get(id=user_id)
                    Group_Members.objects.create(group=group, user=user)
            request.session.pop('selected_members', None)
            request.session.pop('group_form',None)
            messages.success(request, "Group Created Successfully")
            return redirect('assigned')
    selected_ids = request.session.get('selected_members', [])
    selected_members = User_Management.objects.filter(id__in=selected_ids)
    return render(request, "tickets/new_group.html", {
        "selected_members": selected_members,
        'saved_form':saved_form,
    })


@admin_required
def edit_group(request, group_id):
    single_group = get_object_or_404(Assignment_Group, id=group_id)
    saved_form = request.session.get('edit_group_form', {})
    if request.method == 'POST':
        if 'add_member' in request.POST:
            request.session['edit_group_form'] = {
                'name': request.POST.get('name', ''),
                'group_email': request.POST.get('group_email', ''),
                'manager': request.POST.get('manager', ''),
                'parent': request.POST.get('parent', ''),
                'description': request.POST.get('description', ''),
            }
            return redirect(f"{reverse('group_members')}?source_page=edit_group&group_id={group_id}")
        single_group.name = request.POST.get('name')
        single_group.group_email = request.POST.get('group_email')
        single_group.manager = request.POST.get('manager')
        single_group.parent = request.POST.get('parent')
        single_group.description = request.POST.get('description')
        single_group.save()
        submitted_ids = list(map(int, request.POST.getlist('members')))
        existing_ids = list(single_group.members.values_list('user_id', flat=True))
        Group_Members.objects.filter(group=single_group).exclude(user_id__in=submitted_ids).delete()
        for user_id in submitted_ids:
            if user_id not in existing_ids:
                user = User_Management.objects.get(id=user_id)
                Group_Members.objects.create(group=single_group, user=user)
        request.session.pop('selected_members', None)
        messages.success(request, "Group Updated Successfully")
        return redirect('assigned')
    if saved_form:
        single_group.name = saved_form.get('name', single_group.name)
        single_group.group_email = saved_form.get('group_email', single_group.group_email)
        single_group.manager = saved_form.get('manager', single_group.manager)
        single_group.parent = saved_form.get('parent', single_group.parent)
        single_group.description = saved_form.get('description', single_group.description)
    members = single_group.members.select_related('user')
    return render(request, "tickets/edit_group.html", {
        "group": single_group,
        "members": members
    })

@admin_required
def group_members(request):
    users = User_Management.objects.filter(role__iexact='user')
    if request.method == 'POST':
        selected_ids = request.POST.getlist('members')
        selected_ids = list(map(int, selected_ids)) 
        source_page = request.POST.get('source_page')
        group_id = request.POST.get('group_id')
        if source_page == 'edit_group' and group_id and group_id != 'None':
            group_id = int(group_id)
            group = Assignment_Group.objects.get(id=group_id)
            Group_Members.objects.filter(group=group).exclude(user_id__in=selected_ids).delete()
            existing_ids = list(group.members.values_list('user_id', flat=True))
            for uid in selected_ids:
                if uid not in existing_ids:
                    user = User_Management.objects.get(id=uid)
                    Group_Members.objects.create(group=group, user=user)
            request.session.pop('selected_members', None)
            return redirect('edit_group', group_id=group_id)
        request.session['selected_members'] = selected_ids
        return redirect('new_group')
    source_page = request.GET.get('source_page')
    group_id = request.GET.get('group_id')
    session_members = request.session.get('selected_members', [])
    if source_page == 'edit_group' and group_id and group_id != 'None':
        group_id = int(group_id)
        group = Assignment_Group.objects.get(id=group_id)
        if not session_members:
            session_members = list(group.members.values_list('user_id', flat=True))
            request.session['selected_members'] = session_members
    initial_member_ids = session_members or []
    available_users = users.exclude(id__in=initial_member_ids)
    selected_members = User_Management.objects.filter(id__in=initial_member_ids)
    return render(request, "tickets/group_members.html", {
        "users": available_users,
        "initial_selected_members": selected_members,
        "source_page": source_page,
        "group_id": group_id
    })



@admin_required
def delete_group(request,group_id):
    d_group=get_object_or_404(Assignment_Group,id=group_id)
    d_group.delete()
    return redirect('assigned')


#---------------------------USER LISTING, ADDING USER, EDIT AND DELETE-----------------------------

@admin_required
def user_management(request):
    add=User_Management.objects.all()
    return render(request,'user_management/user_management.html',{'add':add})

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
    return render(request,'user_management/create_user.html')

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
    return render(request,'user_management/edit_user.html',context)

@admin_required
def delete_user(request,user_id):
    user=get_object_or_404(User_Management,id=user_id)
    user.delete()
    return redirect('user_management')



#----------------------------------MASTER DATA---------------------------------------------------

@admin_required
def master_data(request):
    return render(request,'master_data/master_data.html')

@admin_required
def school_details(request):
    data=Master_Data.objects.all()
    context={
        'data':data
    }
    return render(request,'master_data/school_details.html',context)

@admin_required
def school_add(request):
    if request.method=='POST':
        name=request.POST.get('name')
        code=request.POST.get('code')
        email=request.POST.get('email')
        phone=request.POST.get('phone')
        if not phone.isdigit() or len(phone) != 10:
            return render(request, 'master_data_add.html', {'error': 'Phone number must be 10 digits.'})
        Master_Data.objects.create(name=name,code=code,email=email,phone=phone)
        messages.success(request,'Details Added')
        return redirect('school_details')
    return render(request,'master_data/school_add.html')

@admin_required
def school_edit(request,master_id):
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
        return redirect('school_details')
    context={
        'single_data':single_master_data
    }
    return render(request,'master_data/school_edit.html',context)

@admin_required
def school_delete(request,master_id):
    master=get_object_or_404(Master_Data,id=master_id)
    master.delete()
    return redirect('school_details')

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
    return render(request,'master_data/group_details.html',context)

@admin_required
def priority_data(request):
    priorities=Priority_Data.objects.all()
    context={
        'priorities':priorities
    }
    return render(request,'master_data/priority_data.html',context)

@admin_required
def priority_add(request):
    if request.method=='POST':
        name=request.POST.get('name')
        time=request.POST.get('time')
        unit=request.POST.get('unit')
        Priority_Data.objects.create(name=name,time=time,unit=unit)
        messages.success(request,'Priority Added')
        return redirect('priority_data')
    return render(request,'master_data/priority_add.html')

def priority_edit(request,priority_id):
    single_priority=get_object_or_404(Priority_Data,id=priority_id)
    if request.method=='POST':
        single_priority.name=request.POST.get('name')
        single_priority.time=request.POST.get('time')
        single_priority.unit=request.POST.get('unit')
        single_priority.save()
        messages.success(request,'Priority Updated')
        return redirect('priority_data')
    context={
        'single_priority':single_priority
    }
    return render(request,'master_data/priority_edit.html',context)

def priority_delete(request,priority_id):
    priority=get_object_or_404(Priority_Data,id=priority_id)
    priority.delete()
    return redirect('priority_data')

def ticket_duration(request):
    durations = Ticket_Duration.objects.select_related('ticket').order_by('-opened_time')
    context = {
        'durations': durations,
    }
    return render(request,'master_data/ticket_duration.html',context)

def delete_duration(request,duration_id):
    duration=get_object_or_404(Ticket_Duration,id=duration_id)
    duration.delete()
    return redirect('ticket_duration')



def school_autofill(request):
    q = request.GET.get('q', '')
    if q:
        # Filter schools by name (case insensitive)
        schools = Master_Data.objects.filter(name__icontains=q).values('name', 'code')[:10]
    else:
        schools = Master_Data.objects.all().values('name', 'code')[:10]
    return JsonResponse(list(schools), safe=False)


#------------------------CALLER DETAILS------------------------------------------
def caller_details(request):
    schools=Master_Data.objects.all()
    callers=Caller_Details.objects.all()
    context={
        'callers':callers,
        'schools':schools
        }
    return render(request,'tickets/caller_details.html',context)   

def add_caller_details(request):
    if request.method == 'POST':
        if 'save' in request.POST:
            caller=Caller_Details.objects.create(
                caller_name=request.POST['caller_name'],
                caller_role=request.POST['caller_role'],
                caller_email=request.POST['caller_email'],
                caller_phone=request.POST['caller_phone'],
                school_name=request.POST['school_name'],
                school_code=request.POST['school_code']
            )
            # request.session['last_caller_name'] = request.POST['caller_name']
            request.session['last_caller_name'] = caller.caller_name  # Name for display
            request.session['last_caller_id'] = caller.id  # NEW: ID for FK
            request.session['last_school_name'] = request.POST['school_name']
            request.session['last_school_code'] = request.POST['school_code']
    return redirect(reverse('create') + '?from_caller=1')    

def delete_caller(request,caller_id):
    caller=get_object_or_404(Caller_Details,id=caller_id)
    caller.delete()
    return redirect('caller_details')

#------------------------OVERVIEW AND REPORTS------------------------------------------
def overview(request):
    return render(request,'overview.html')

def overview_api_view(request):
    qs = Create_Ticket.objects.all()
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    week_start = today_start - timedelta(days=today_start.weekday())

    period = request.GET.get('period')
    month = request.GET.get('month')
    start_str = request.GET.get('start')
    end_str = request.GET.get('end')

    # Apply ONE filter only (priority order)
    if start_str and end_str:
        try:
            start = datetime.strptime(start_str, '%Y-%m-%d').date()
            end = datetime.strptime(end_str, '%Y-%m-%d').date()
            qs = qs.filter(created_at__date__gte=start, created_at__date__lte=end)
            # ↑ Use created_at, not updated_at!
        except:
            pass
    elif month and month.lower() != 'select month':
        month_map = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        m = month_map.get(month.lower())
        if m:
            qs = qs.filter(created_at__month=m)
    elif period == 'today':
        qs = qs.filter(created_at__gte=today_start)
    elif period == 'yesterday':
        qs = qs.filter(created_at__gte=yesterday_start, created_at__lt=today_start)
    elif period == 'week':
        qs = qs.filter(created_at__gte=week_start)

    # Now count from the correct queryset
    total = qs.count()
    open = qs.filter(state__in=['new', 'in progress', 'on hold']).count()
    in_progress = qs.filter(state='in progress').count()
    resolved = qs.filter(state='resolved').count()
    closed = qs.filter(state='closed').count()

    critical = qs.filter(priority__name='critical').count()
    high = qs.filter(priority__name='high').count()
    moderate = qs.filter(priority__name='moderate').count()
    low = qs.filter(priority__name='low').count()

    overdue = qs.filter(state__in=['new', 'in progress', 'on hold'], due_at__lt=now).count()
    # in_progress_critical = qs.filter(state='in progress', priority__name='critical').count()

    return JsonResponse({
        "total": total,
        "open": open,
        "inProgress": in_progress,
        "resolved": resolved,
        "closed": closed,
        "overdue": overdue,
        "critical": critical,

        "priority": {
            "critical": critical,
            "high": high,
            "moderate": moderate,
            "low": low
        }
      
    })


def priority_tickets_api(request):
    priority = request.GET.get('priority')

    qs = Create_Ticket.objects.select_related('priority')

    if priority:
        qs = qs.filter(priority__name__iexact=priority)

    qs = qs.order_by('-created_at')  # limit for UI
  
    tickets = []
    for t in qs:
        tickets.append({
            'id': t.id,
            'number': t.number,
            'short_description': t.short_description,
            'caller': t.caller or '-',
            'state': t.state,
        })

    return JsonResponse({'tickets': tickets})

def reports(request):
    schools=Master_Data.objects.all().order_by('name')  
    qs=(Create_Ticket.objects.values('category').annotate(total=Count('id')).order_by('category'))
    category_display = dict(Category_Choices)
    labels=[category_display.get(row['category'], row['category']) for row in qs]
    data=[row['total'] for row in qs]
    counts=[row['total'] for row in qs]

    web_count= Create_Ticket.objects.filter(platform='web application').count()
    mobile_count=Create_Ticket.objects.filter(platform='mobile application').count()
    total_tickets=web_count + mobile_count

    context = {
        'schools': schools,
        'category_labels': mark_safe(json.dumps(labels)),
        'category_data': mark_safe(json.dumps(data)),
        'category_legend': list(zip(labels, counts)),
        'web_count':     web_count,
        'mobile_count':  mobile_count,
        'total_tickets': total_tickets,
    }
    return render(request,'reports.html',context)

def reports_data(request):
    school = request.GET.get('school')   # school name (string)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    tickets = Create_Ticket.objects.all()

    # filter by school
    if school:
        tickets = tickets.filter(school_name=school)

    # filter by date
    if start_date and end_date:
        tickets = tickets.filter(
            created_at__date__range=[start_date, end_date]
        )

    qs = tickets.values('category').annotate(total=Count('id')).order_by('category')

    category_display = dict(Category_Choices)
    category_labels = [category_display.get(row['category']) for row in qs]
    category_data = [row['total'] for row in qs]

    web_count = tickets.filter(platform='web application').count()
    mobile_count = tickets.filter(platform='mobile application').count()

    return JsonResponse({
        'category_labels': category_labels,
        'category_data': category_data,
        'web_count': web_count,
        'mobile_count': mobile_count,
        'total_tickets': web_count + mobile_count,
    })




def category_table(request):
    return redirect(request,'master_data/category_table.html')
def modules_table(request):
    return redirect(request,'master_data/modules_table.html')