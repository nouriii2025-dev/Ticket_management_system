
from django.contrib import admin
from django.urls import path
from servicedeskapp import views

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

    path('group_members',views.group_members,name='group_members')

]
