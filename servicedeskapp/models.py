from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from django.core.validators import RegexValidator
from datetime import timedelta

class Sign_up(models.Model):
    name = models.CharField(max_length=200, null=True)
    username = models.CharField(max_length=200, unique=True, null=True)
    email = models.EmailField(max_length=200, unique=True, null=True)
    password = models.CharField(max_length=200, null=True)
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    def __str__(self):
        return self.email

Category_Choices=[
    ('inquiry/help','Inquiry/Help'),
    ('software','Software'),
    ('hardware','Hardware'),
    ('network','Network'),
    ('database','Database'),
    ('other', 'Other'),
]
Channel_Choices=[
    ('email','Email'),
    ('phone','Phone'),
    ('self-service','Self-service'),
    ('chat','Chat'),
    ('virtual agent','Virtual Agent'),
    ('walk-in','Walk-in'),
    ('other', 'Other'),
]
Modules_Choices=[
    ('hrms','HRMS'),
    ('admin','Admin'),
    ('fee','Fee'),
    ('teacher','Teacher'),
    ('transport','Transport'),
    ('library','Library'),
    ('asset management','Asset Management'),
    ('application tracker','Application Tracker'),
    ('store','Store'),
    ('visitor management','Visitor Management'),
    ('other', 'Other'),
]
State_Choices=[
    ('new','New'),
    ('in progress','In Progress'),
    ('on hold','On Hold'),
    ('resolved','Resolved'),
    ('closed','Closed'),
    ('canceled','Canceled'),
]
Impact_Choices=[
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]
Urgency_Choices=Impact_Choices
Platform_Choices=[
    ('web application','Web Application'),
    ('mobile application','Mobile Application'),
]
Resolution_Code_Choices=[
    ('duplicate','Duplicate'),
    ('known error','Known error'),
    ('no resolution provided','No resolution provided'),
    ('resolved by caller','Resolved by caller'),
    ('resolved by change','Resolved by change'),
    ('resolved by problem','Resolved by problem'),
    ('resolved by request','Resolved by request'),
    ('solution provided','Solution Provided'),
    ('workaround provided','Workaround provided'),
    ('user error','User error'),
]

class Create_Ticket(models.Model):
    category=models.CharField(max_length=100,choices=Category_Choices,blank=True,null=True)
    channel=models.CharField(max_length=100,choices=Channel_Choices,blank=True,default='email',null=True)
    modules=models.CharField(max_length=100,blank=True,null=True,choices=Modules_Choices)
    state=models.CharField(max_length=100,choices=State_Choices,null=True,blank=True,default='')
    caller=models.CharField(max_length=100,blank=True,null=True)
    platform=models.CharField(max_length=100,choices=Platform_Choices,blank=True,null=True)
    impact=models.CharField(max_length=100,choices=Impact_Choices,default='low')
    number = models.CharField(max_length=50,blank=True,null=True)
    school_name=models.CharField(max_length=100,blank=True,null=True)
    school_code=models.CharField(max_length=100,blank=True,null=True)
    urgency=models.CharField(max_length=100,choices=Urgency_Choices,default='low')
    created_at=models.DateTimeField(auto_now_add=True)
    priority = models.ForeignKey('Priority_Data', on_delete=models.SET_NULL, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    assignment_group = models.CharField(max_length=100,blank=True, null=True)
    created_by=models.CharField(max_length=100,null=True,blank=True)
    updated_by = models.CharField(max_length=100,blank=True,null=True)
    assigned_to = models.CharField(max_length=100,blank=True,null=True)
    short_description = models.CharField(max_length=255,default='')
    description = models.TextField(blank=True,null=True)
    additional_comments = models.TextField(blank=True,null=True)
    work_notes = models.TextField(blank=True,null=True)
    parent_incident = models.CharField(max_length=100,blank=True,null=True)
    problem=models.CharField(max_length=100,blank=True,null=True)
    change_request=models.CharField(max_length=100,blank=True,null=True)
    caused_by_change=models.CharField(max_length=100,blank=True,null=True)
    resolved_by=models.CharField(max_length=100,blank=True,null=True)
    resolution_code=models.CharField(max_length=100,choices=Resolution_Code_Choices,default='duplicate')
    resolution_notes=models.TextField(blank=True,null=True)
    caller_details = models.ForeignKey('Caller_Details',on_delete=models.SET_NULL,null=True,blank=True,related_name='tickets')
    due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    def __str__(self):
        return f" {self.number}: {self.short_description}"
    def save(self, *args, **kwargs):
        sla = None
        if self.priority and self.priority.time is not None:
            if self.priority.unit == 'hours':
                sla = timedelta(hours=self.priority.time)
            elif self.priority.unit == 'days':
                sla = timedelta(days=self.priority.time)
            elif self.priority.unit == 'minutes':
                sla = timedelta(minutes=self.priority.time)

        is_new = self.pk is None
        super().save(*args, **kwargs)

        # Only calculate due_at AFTER created_at exists
        if sla and self.created_at:
            self.due_at = self.created_at + sla
            # Update only this field
            super().save(update_fields=['due_at'])
    
#group creation
class Assignment_Group(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True)
    group_email=models.EmailField(max_length=100,null=True,blank=True)
    manager=models.CharField(max_length=100,null=True,blank=True)
    parent=models.CharField(max_length=100,null=True,blank=True)
    description=models.TextField(null=True,blank=True)
    def __str__(self):
        return self.name

class Group_Members(models.Model):
    group = models.ForeignKey(Assignment_Group, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey('User_Management', on_delete=models.CASCADE, null=True, blank=True)
    def __str__(self):
        return self.user.name if self.user else "Unknown User"

#actvity tracking    
class Activity(models.Model):
    ticket=models.ForeignKey(Create_Ticket,on_delete=models.CASCADE,related_name='activities')
    user=models.CharField(max_length=100, null=True, blank=True)
    action=models.CharField(max_length=100,default="Fields changed")
    created_at=models.DateTimeField(default=timezone.now,null=True, blank=True)
    def __str__(self):
        return f"{self.user} - {self.action}" 
    
class Field_Change(models.Model):
    activity=models.ForeignKey(Activity,on_delete=models.CASCADE,related_name='changes')
    field_name=models.CharField(max_length=100)
    old_value=models.TextField(null=True,blank=True)
    new_value=models.TextField(null=True,blank=True)
    def __str__(self):
        return self.field_name

#user creation
phone_validator = RegexValidator(
    regex=r'^\d{10}$',
    message="Phone number must be exactly 10 digits and contain only numbers."
)

Role_Choices=[
    ('user','User'),
    ('admin','Admin'),
    ('other','Other'),
] 
class User_Management(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True)
    username=models.CharField(max_length=100,null=True,blank=True)
    email=models.EmailField(max_length=100,null=True,blank=True)
    phone=models.CharField(validators=[phone_validator],max_length=10,null=True,blank=True)
    role=models.CharField(max_length=100,choices=Role_Choices,null=True,blank=True,default='user')
    created_at=models.DateTimeField(auto_now_add=True)
    last_login=models.DateTimeField(null=True, blank=True)
    password=models.CharField(max_length=300,null=True,blank=True)
    def __str__(self):
        return self.name or "Unnamed User"
    def get_email_field_name(self):
        return "email"
    def set_password(self, raw_password):
        self.password = make_password(raw_password)

   
class Master_Data(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True)
    code=models.CharField(max_length=100,null=True,blank=True)
    email=models.EmailField(max_length=100,null=True,blank=True)
    phone=models.CharField(validators=[phone_validator],max_length=10,null=True,blank=True)
    def __str__(self):
        return self.name
    
Unit_Choices=[
    ('hours','Hours'),
    ('days','Days'),
    ('minutes','Minutes'),
]
Priority_Choices=[
    ('low','Low'),
    ('moderate','Moderate'),
    ('high','High'),
    ('critical','Critical'),
]
class Priority_Data(models.Model):
    name=models.CharField(max_length=100,null=True,blank=True,choices=Priority_Choices)
    time=models.IntegerField(null=True,blank=True)
    unit=models.CharField(max_length=50,null=True,blank=True,choices=Unit_Choices)
    def __str__(self):
        return self.get_name_display()
    
class Ticket_Duration(models.Model):
    ticket=models.OneToOneField(Create_Ticket,on_delete=models.CASCADE,related_name='duration')
    ticket_number=models.CharField(max_length=100,null=True,blank=True)
    category=models.CharField(max_length=100,null=True,blank=True)
    modules=models.CharField(max_length=100,null=True,blank=True)
    opened_time=models.DateTimeField(null=True,blank=True)
    resolved_time=models.DateTimeField(null=True,blank=True)
    duration = models.DurationField(null=True, blank=True)
    def __str__(self):
        return self.ticket_number
    def formatted_duration(self):
        if not self.duration:
            return "-"

        total_seconds = int(self.duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = (total_seconds % 60)

        if hours and minutes:
            return f"{hours} hour{'s' if hours > 1 else ''} {minutes} minute{'s' if minutes > 1 else ''}"
        elif hours:
            return f"{hours} hour{'s' if hours > 1 else ''}"
        elif minutes:
            return f"{minutes} minute{'s' if minutes > 1 else ''}"
        else:
            return f"{seconds} second{'s' if seconds > 1 else ''}"
        

    
class Caller_Details(models.Model):
    caller_name=models.CharField(max_length=100,null=True,blank=True)
    caller_role=models.CharField(max_length=100,blank=True,null=True)
    caller_email=models.EmailField(max_length=100,null=True,blank=True)
    caller_phone=models.CharField(validators=[phone_validator],max_length=10,null=True,blank=True)
    school_name=models.CharField(max_length=100,null=True,blank=True)
    school_code=models.CharField(max_length=100,null=True,blank=True)
    def __str__(self):
        return self.caller_name

