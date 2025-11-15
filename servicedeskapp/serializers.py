from rest_framework import serializers
from .models import *

class CreateTicketSerializer(serializers.ModelSerializer):
    activities = serializers.SerializerMethodField()

    class Meta:
        model = Create_Ticket
        fields = '__all__'

    def get_activities(self, obj):
        from .serializers import ActivitySerializer
        activities = obj.activities.all()
        return ActivitySerializer(activities, many=True).data


class AssignmentGroupSerializer(serializers.ModelSerializer):
    members = serializers.SerializerMethodField()

    class Meta:
        model = Assignment_Group
        fields = '__all__'

    def get_members(self, obj):
        from .serializers import GroupMemberSerializer
        members = obj.members.all()
        return GroupMemberSerializer(members, many=True).data


class GroupMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group_Members
        fields = '__all__'


class ActivitySerializer(serializers.ModelSerializer):
    changes = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = '__all__'

    def get_changes(self, obj):
        from .serializers import FieldChangeSerializer
        changes = obj.changes.all()
        return FieldChangeSerializer(changes, many=True).data



class FieldChangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Field_Change
        fields = '__all__'


class UserManagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = User_Management
        fields = '__all__'


class MasterDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = Master_Data
        fields = '__all__'
