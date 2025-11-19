
from django.contrib import admin
from django.urls import path
from servicedeskapp import views
from servicedeskapp import apiviews

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup',views.sign_up,name='signup'),
    path('',views.login,name='login'),
    path('reset',views.reset_password,name='reset'),
    path('logout',views.logout,name='logout'),

    path('dashboard',views.dashboard,name='dashboard'),
    path('create',views.create_ticket,name='create'),
    path('update<int:ticket_id>',views.update_ticket,name='update'),

    path('assigned',views.assigned_group,name='assigned'),
    path('new_group',views.new_group,name='new_group'),
    path('edit_group/<int:group_id>/',views.edit_group,name='edit_group'),
    path('delete_group<int:group_id>',views.delete_group,name='delete_group'),
    path('preview',views.preview,name='preview'),

    path('user_management',views.user_management,name='user_management'),
    path('create_user',views.create_user,name='create_user'),
    path('edit_user<int:user_id>',views.edit_user,name='edit_user'),
    path('delete_user<int:user_id>',views.delete_user,name='delete_user'),

    path('parent_incident',views.parent_incident,name='parent_incident'),
    path('delete_tickets',views.delete_tickets,name='delete_tickets'),

    path('group_members',views.group_members,name='group_members'),

    path('school_details',views.school_details,name='school_details'),
    path('school_add',views.school_add,name='school_add'),
    path('school_edit<int:master_id>',views.school_edit,name='school_edit'),
    path('school_delete<int:master_id>',views.school_delete,name='school_delete'),
    path('master_data',views.master_data,name='master_data'),
    path('group_details',views.group_details,name='group_details'),
    
    path('school_autofill',views.school_autofill,name='school_autofill'),

    #rest api
     path('auth/signup/', apiviews.sign_up_api, name='api_signup'),
    path('auth/login/', apiviews.login_api, name='api_login'),
    path('auth/reset-password/', apiviews.reset_password_api, name='api_reset_password'),

    path('tickets/', apiviews.dashboard_api, name='api_dashboard'), 
    path('tickets/create/', apiviews.create_ticket_api, name='api_create_ticket'), 
    path('tickets/delete-multiple/', apiviews.delete_tickets_api, name='api_delete_tickets'),
    path('tickets/<int:ticket_id>/', apiviews.update_ticket_api, name='api_update_ticket'), 
    path('tickets/parent-lookup/', apiviews.parent_incident_api, name='api_parent_incident_lookup'),

    path('groups/', apiviews.assigned_group_api, name='api_list_groups'),
    path('groups/create/', apiviews.new_group_api, name='api_create_group'),
    path('groups/<int:group_id>/', apiviews.edit_group_api, name='api_edit_group'),
    path('groups/<int:group_id>/delete/',apiviews.delete_group_api, name='api_delete_group'),
    path('groups/manage-members/', apiviews.group_members_api, name='api_manage_group_members'),

    path('users/', apiviews.user_management_api, name='api_user_management'),
    path('users/create/', apiviews.create_user_api, name='api_create_user'),
    path('users/<int:user_id>/', apiviews.edit_user_api, name='api_edit_user'),
    path('users/<int:user_id>/delete/', apiviews.delete_user_api, name='api_delete_user'),

    path('master-data/', apiviews.master_data_api, name='api_master_data'),
    path('master-data/add/', apiviews.master_data_add_api, name='api_master_data_add'),
    path('master-data/<int:master_id>/', apiviews.master_data_edit_api, name='api_master_data_edit'),
    path('master-data/<int:master_id>/delete/', apiviews.master_data_delete_api, name='api_master_data_delete'),


]
