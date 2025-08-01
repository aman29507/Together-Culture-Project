"""
Django admin configuration for Together Culture CRM.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Member, Interest, InterestHistory, ActivityLog


# Unregister the default User admin
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Enhanced User admin with member profile integration.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'member_status', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    
    def member_status(self, obj):
        """Display member status if exists."""
        try:
            member = obj.member_profile
            status_colors = {
                'pending': 'orange',
                'approved': 'green',
                'rejected': 'red',
                'inactive': 'gray'
            }
            color = status_colors.get(member.status, 'black')
            return format_html(
                '<span style="color: {};">{}</span>',
                color,
                member.get_status_display()
            )
        except Member.DoesNotExist:
            return format_html('<span style="color: gray;">No Profile</span>')
    
    member_status.short_description = 'Member Status'


class InterestHistoryInline(admin.TabularInline):
    """
    Inline for viewing interest history in member admin.
    """
    model = InterestHistory
    extra = 0
    readonly_fields = ('timestamp', 'changed_by')
    fields = ('interest', 'action', 'changed_by', 'timestamp', 'notes')
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """
    Admin interface for Member model.
    """
    list_display = (
        'full_name', 'email', 'status', 'interests_display', 
        'date_applied', 'date_approved', 'approved_by'
    )
    list_filter = ('status', 'date_applied', 'date_approved', 'interests')
    search_fields = ('user__first_name', 'user__last_name', 'user__email', 'bio')
    readonly_fields = ('date_applied', 'date_approved', 'user_link', 'profile_picture_preview')
    filter_horizontal = ('interests',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user_link', 'status', 'approved_by')
        }),
        ('Profile Information', {
            'fields': ('bio', 'phone_number', 'profile_picture', 'profile_picture_preview')
        }),
        ('Interests', {
            'fields': ('interests',)
        }),
        ('Timeline', {
            'fields': ('date_applied', 'date_approved'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [InterestHistoryInline]
    
    actions = ['approve_members', 'reject_members']
    
    def full_name(self, obj):
        """Display member's full name."""
        return obj.full_name
    full_name.short_description = 'Name'
    
    def email(self, obj):
        """Display member's email."""
        return obj.email
    email.short_description = 'Email'
    
    def interests_display(self, obj):
        """Display member's interests as badges."""
        interests = obj.interests.all()
        if not interests:
            return 'None'
        
        badges = []
        for interest in interests:
            badges.append(f'<span class="badge badge-primary">{interest.get_name_display()}</span>')
        
        return format_html(' '.join(badges))
    interests_display.short_description = 'Interests'
    
    def user_link(self, obj):
        """Link to user admin page."""
        if obj.user:
            url = reverse('admin:auth_user_change', args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'No User'
    user_link.short_description = 'User Account'
    
    def profile_picture_preview(self, obj):
        """Display profile picture preview."""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.profile_picture.url
            )
        return 'No Picture'
    profile_picture_preview.short_description = 'Profile Picture'
    
    def approve_members(self, request, queryset):
        """Bulk approve members."""
        updated = 0
        for member in queryset.filter(status='pending'):
            member.approve_membership(request.user)
            updated += 1
        
        self.message_user(
            request,
            f'{updated} member(s) were successfully approved.'
        )
    approve_members.short_description = 'Approve selected members'
    
    def reject_members(self, request, queryset):
        """Bulk reject members."""
        updated = queryset.filter(status='pending').update(status='rejected')
        self.message_user(
            request,
            f'{updated} member(s) were rejected.'
        )
    reject_members.short_description = 'Reject selected members'


@admin.register(Interest)
class InterestAdmin(admin.ModelAdmin):
    """
    Admin interface for Interest model.
    """
    list_display = ('get_name_display', 'name', 'member_count', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'member_count')
    
    def member_count(self, obj):
        """Display count of members with this interest."""
        count = obj.members.filter(status='approved').count()
        return f'{count} members'
    member_count.short_description = 'Member Count'


@admin.register(InterestHistory)
class InterestHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Interest History.
    """
    list_display = ('member', 'interest', 'action', 'changed_by', 'timestamp')
    list_filter = ('action', 'interest', 'timestamp')
    search_fields = ('member__user__first_name', 'member__user__last_name', 'member__user__email')
    readonly_fields = ('timestamp',)
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """
    Admin interface for Activity Log.
    """
    list_display = ('user', 'action', 'target_member', 'timestamp', 'ip_address')
    list_filter = ('action', 'timestamp')
    search_fields = ('user__username', 'description', 'target_member__user__email')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Custom admin site styling
admin.site.site_header = "Together Culture CRM"
admin.site.site_title = "Together Culture CRM"
admin.site.index_title = "Administration Dashboard"