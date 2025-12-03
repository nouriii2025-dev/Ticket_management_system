from django.shortcuts import get_object_or_404
from .models import *
from .serializers import * 
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Max
from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import re
from django.core.exceptions import ValidationError
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth.tokens import PasswordResetTokenGenerator

@api_view(['POST'])
def sign_up_api(request):
    if request.method == 'POST':
        name = request.data.get('name')
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')

        if password != confirm_password:
            return Response({"error": "Passwords don't match"}, status=status.HTTP_400_BAD_REQUEST)
        
        if Sign_up.objects.filter(email=email).exists():
            return Response({"error": "Account with same email already exists"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = Sign_up.objects.create(name=name, username=username, email=email)
            user.set_password(password) 
            user.save()
            return Response({"message": "Sign up successful, please login"}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": f"An error occurred: {e}"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def login_api(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if not username or not password:
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = User_Management.objects.get(username=username)
        if check_password(password, user.password):
            user_data = {
                "username": user.username,
                "name": user.name,
                "role": user.role,
                "message": "Login successful"
            }
            return Response(user_data, status=status.HTTP_200_OK)        
        else:
            return Response(
                {"error": "Invalid password"},
                status=status.HTTP_401_UNAUTHORIZED
            )
    except User_Management.DoesNotExist:
        return Response(
            {"error": "User does not exist"},
            status=status.HTTP_404_NOT_FOUND
        )


token_generator = PasswordResetTokenGenerator()

@api_view(['POST'])
def reset_password_api(request):
    email = request.data.get("email")
    if not email:
        return Response(
            {"error": "Email is required"},
            status=status.HTTP_400_BAD_REQUEST
        )
    try:
        user = User_Management.objects.get(email=email)
    except User_Management.DoesNotExist:
        return Response(
            {"error": "Email not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    uidb64 = urlsafe_base64_encode(force_bytes(user.id))
    token = token_generator.make_token(user)
    reset_url = request.build_absolute_uri(
        reverse("reset_confirm", kwargs={"uidb64": uidb64, "token": token})
    )
    send_mail(
        subject="Password Reset Instructions",
        message=f"Click the link to reset your password:\n{reset_url}\n\nValid for 10 minutes.",
        from_email="your-email@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )
    return Response(
        {"message": "Reset link sent! Check your email."},
        status=status.HTTP_200_OK
    )





@api_view(['GET', 'POST'])
def dashboard_api(request):
    if request.method == 'GET':
        all_tickets = Create_Ticket.objects.all().order_by('-created_at')
        paginator = Paginator(all_tickets, 8) 
        page_number = request.query_params.get('page', 1)
        try:
            page_obj = paginator.get_page(page_number)
        except Exception:
            return Response({"error": "Invalid page number"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = CreateTicketSerializer(page_obj.object_list, many=True)
        
        return Response({
            'count': paginator.count,
            'page_number': page_obj.number,
            'num_pages': paginator.num_pages,
            'next': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous': page_obj.previous_page_number() if page_obj.has_previous() else None,
            'tickets': serializer.data
        })

@api_view(['POST'])
def delete_tickets_api(request):
    if request.method == 'POST':
        selected_ids = request.data.get('selected_tickets', [])       
        if not selected_ids:
            return Response({"error": "No tickets selected."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            count, _ = Create_Ticket.objects.filter(id__in=selected_ids).delete()
            return Response({"message": f"{count} ticket(s) deleted successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to delete tickets: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
def create_ticket_api(request):
    def generate_next_number():
        latest_ticket_number = Create_Ticket.objects.aggregate(max_number=Max('number'))['max_number']
        if latest_ticket_number:
            match = re.search(r'(\d+)$', latest_ticket_number)
            if match:
                next_num = int(match.group(1)) + 1
            else:
                next_num = 10001
        else:
            next_num = 10001
        return f'INC{next_num:07d}'
    if request.method == 'POST':
        request.data._mutable = True
        request.data['number'] = generate_next_number()
        if 'username' in request.session:
             request.data['created_by'] = request.session.get('username')

        serializer = CreateTicketSerializer(data=request.data)
        if serializer.is_valid():
            try:
                ticket = serializer.save()
                return Response({
                    "message": "Ticket Added successfully", 
                    "ticket_number": ticket.number,
                    "ticket_id": ticket.id
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        next_number = generate_next_number()
        selected_group = request.query_params.get('assignment_group', '')
        parent_incident = request.query_params.get('parent_incident', '')
        
        group_members_data = []
        if selected_group:
            try:
                group = Assignment_Group.objects.get(name=selected_group)
                group_members = Group_Members.objects.filter(group=group)
                group_members_data = GroupMemberSerializer(group_members, many=True).data
            except Assignment_Group.DoesNotExist:
                pass
        return Response({
            'next_number': next_number,
            'selected_group': selected_group,
            'group_members': group_members_data,
            'parent_incident': parent_incident,
            'category_choices': Category_Choices,
            'channel_choices': Channel_Choices,
        }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
def update_ticket_api(request, ticket_id):
    single_ticket = get_object_or_404(Create_Ticket, id=ticket_id)

    if request.method == 'GET':
        serializer = CreateTicketSerializer(single_ticket)
        activities = single_ticket.activities.all().order_by('-created_at').prefetch_related('changes')
        activity_serializer = ActivitySerializer(activities, many=True)
        
        selected_group = request.query_params.get('assignment_group', single_ticket.assignment_group)

        return Response({
            'ticket': serializer.data,
            'activities': activity_serializer.data,
            'selected_group': selected_group,
        })
    
    elif request.method == 'PUT':
        old_values = {field.name: str(getattr(single_ticket, field.name)) 
                      for field in single_ticket._meta.fields if field.name not in ('id', 'created_at', 'updated_at', 'number', 'created_by')}
        request.data._mutable = True
        if 'username' in request.session:
            request.data['updated_by'] = request.session.get('username')
        
        serializer = CreateTicketSerializer(single_ticket, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        updated_ticket = serializer.save()

        fields_to_check = [
            'category', 'channel', 'sub_category', 'state', 'caller','caller_category','impact', 
            'school_name', 'urgency', 'school_code', 'priority', 'assignment_group', 
            'assigned_to', 'short_description', 'description', 
            'additional_comments', 'work_notes'
        ]
        
        field_changes = []
        for field in fields_to_check:
            old = old_values.get(field)
            new = str(getattr(updated_ticket, field))
            
            if old != new: 
                field_changes.append({
                    'field_name': field,
                    'old_value': old if old is not None else "",
                    'new_value': new if new is not None else ""
                })

        if field_changes:
            activity_record = Activity.objects.create(
                ticket=updated_ticket,
                user=updated_ticket.updated_by,
                action="Field changes"
            )
            
            Field_Change.objects.bulk_create([
                Field_Change(
                    activity=activity_record,
                    field_name=change['field_name'],
                    old_value=change['old_value'],
                    new_value=change['new_value']
                ) for change in field_changes
            ])

        return Response({"message": "Updated Successfully", "ticket": CreateTicketSerializer(updated_ticket).data}, status=status.HTTP_200_OK)


@api_view(['GET'])
def assigned_group_api(request):
    search = request.query_params.get('q', '')
    
    if search:
        groups = Assignment_Group.objects.filter(name__icontains=search)
    else:
        groups = Assignment_Group.objects.all()
        
    serializer = AssignmentGroupSerializer(groups, many=True)
    source_page = request.query_params.get('source_page')
    ticket_id = request.query_params.get('ticket_id')
    
    return Response({
        'groups': serializer.data,
        'source_page': source_page,
        'ticket_id': ticket_id,
    })


@api_view(['GET', 'POST'])
def new_group_api(request):    
    if request.method == 'POST':
        serializer = AssignmentGroupSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)            
        group = serializer.save()
        member_ids = request.data.get('members', [])         
        member_objects = User_Management.objects.filter(id__in=member_ids)
        Group_Members.objects.bulk_create([
            Group_Members(group=group, name=user.name) for user in member_objects
        ])
        if 'selected_members' in request.session:
            del request.session['selected_members']
            
        return Response({"message": "Group created successfully", "group": AssignmentGroupSerializer(group).data}, status=status.HTTP_201_CREATED)
        
    elif request.method == 'GET':
        selected_member_ids = request.session.get('selected_members', [])
        selected_members = User_Management.objects.filter(id__in=selected_member_ids)
        selected_members_data = UserManagementSerializer(selected_members, many=True).data 
        
        return Response({'selected_members': selected_members_data}, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
def edit_group_api(request, group_id):
    """
    GET: Retrieve single group and its members with search.
    PUT: Update a single group and manage its members.
    """
    single_group = get_object_or_404(Assignment_Group, id=group_id)
    
    if request.method == 'GET':
        members = single_group.members.all()
        search = request.query_params.get('q', '')
        if search:
            members = members.filter(name__icontains=search)
            
        group_serializer = AssignmentGroupSerializer(single_group)
        members_serializer = GroupMemberSerializer(members, many=True)
        
        return Response({
            'group': group_serializer.data,
            'members': members_serializer.data
        })
        
    elif request.method == 'PUT':
        group_serializer = AssignmentGroupSerializer(single_group, data=request.data, partial=True)
        if not group_serializer.is_valid():
            return Response(group_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        updated_group = group_serializer.save()
        member_names = request.data.get('member_names', []) 
        submitted_members = {name.strip() for name in member_names if name.strip()}
        
        existing_members = set(updated_group.members.values_list('name', flat=True))
        
        members_to_delete = existing_members - submitted_members
        members_to_add = submitted_members - existing_members
        
        if members_to_delete:
            Group_Members.objects.filter(group=updated_group, name__in=members_to_delete).delete()
            
        if members_to_add:
            Group_Members.objects.bulk_create([
                Group_Members(group=updated_group, name=name) for name in members_to_add
            ])

        return Response({"message": "Updated Successfully", "group": AssignmentGroupSerializer(updated_group).data}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
def delete_group_api(request, group_id):
    d_group = get_object_or_404(Assignment_Group, id=group_id)
    d_group.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['GET'])
def user_management_api(request):
    """List all users in User_Management."""
    users = User_Management.objects.all()
    serializer = UserManagementSerializer(users, many=True)
    return Response({'users': serializer.data})


@api_view(['POST'])
def create_user_api(request):
    data = request.data
    password = data.get('password')
    confirm_password = data.get('confirm_password')
    phone = data.get('phone', '')

    if password != confirm_password:
        return Response({"error": "Passwords don't match"}, status=status.HTTP_400_BAD_REQUEST)
    if not phone.isdigit() or len(phone) != 10:
        return Response({'error': 'Phone number must be exactly 10 digits.'}, status=status.HTTP_400_BAD_REQUEST)
    hashed_password = make_password(password)

    serializer = UserManagementSerializer(data=data)
    if serializer.is_valid():
        try:
            user = serializer.save(password=hashed_password)
            return Response({"message": "User created successfully", "user": UserManagementSerializer(user).data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
def edit_user_api(request, user_id):
    single_user = get_object_or_404(User_Management, id=user_id)
    
    if request.method == 'GET':
        serializer = UserManagementSerializer(single_user)
        return Response(serializer.data)
        
    elif request.method == 'PUT':
        data = request.data
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if password and password.strip():
            if password != confirm_password:
                return Response({"error": "Passwords don't match"}, status=status.HTTP_400_BAD_REQUEST)
        phone = data.get('phone', single_user.phone)
        if not phone.isdigit() or len(phone) != 10:
            return Response({'error': 'Phone number must be exactly 10 digits.'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = UserManagementSerializer(single_user, data=data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            if password and password.strip():
                updated_user.password = make_password(password)
                updated_user.save(update_fields=['password']) 
                
            return Response({"message": "Updated successfully", "user": UserManagementSerializer(updated_user).data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_user_api(request, user_id):
    user = get_object_or_404(User_Management, id=user_id)
    user.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def parent_incident_api(request):
    all_tickets = Create_Ticket.objects.all().order_by('-created_at')
    data = []
    for ticket in all_tickets:
        data.append({
            'id': ticket.id,
            'number': ticket.number,
            'short_description': ticket.short_description,
            'assigned_to': ticket.assigned_to,
            'assignment_group': ticket.assignment_group,
        })

    return Response({
        'tickets': data,
        'ticket_count': all_tickets.count(),
    })


@api_view(['GET', 'POST'])
def group_members_api(request):
    users = User_Management.objects.filter(role__iexact='user')
    
    if request.method == 'POST':
        selected_members_ids = request.data.get('members', []) 
        
        request.session['selected_members'] = selected_members_ids 
        return Response({"message": "Selected members saved temporarily for group creation."}, status=status.HTTP_200_OK)

    elif request.method == 'GET':
        initial_member_ids = request.session.get('selected_members', [])

        available_users = users.exclude(id__in=initial_member_ids)
        selected_members = User_Management.objects.filter(id__in=initial_member_ids)
        
        available_users_data = UserManagementSerializer(available_users, many=True).data
        selected_members_data = UserManagementSerializer(selected_members, many=True).data
        
        return Response({
            'users': available_users_data,
            'initial_selected_members': selected_members_data 
        })



@api_view(['GET'])
def master_data_api(request):
    data = Master_Data.objects.all()
    serializer = MasterDataSerializer(data, many=True)
    return Response({'data': serializer.data})


@api_view(['POST'])
def master_data_add_api(request):
    phone = request.data.get('phone', '')
    if not phone.isdigit() or len(phone) != 10:
        return Response({'error': 'Phone number must be exactly 10 digits.'}, status=status.HTTP_400_BAD_REQUEST)
        
    serializer = MasterDataSerializer(data=request.data)
    if serializer.is_valid():
        record = serializer.save()
        return Response({"message": "Details Added", "record": serializer.data}, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT'])
def master_data_edit_api(request, master_id):
    single_master_data = get_object_or_404(Master_Data, id=master_id)
    
    if request.method == 'GET':
        serializer = MasterDataSerializer(single_master_data)
        return Response({'single_data': serializer.data})
        
    elif request.method == 'PUT':
        phone = request.data.get('phone', single_master_data.phone)
        if not phone.isdigit() or len(phone) != 10:
            return Response({'error': 'Phone number must be exactly 10 digits.'}, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = MasterDataSerializer(single_master_data, data=request.data, partial=True)
        if serializer.is_valid():
            updated_data = serializer.save()
            return Response({"message": "Updated Successfully", "record": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def master_data_delete_api(request, master_id):
    master = get_object_or_404(Master_Data, id=master_id)
    master.delete() 
    return Response(status=status.HTTP_204_NO_CONTENT)