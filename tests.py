"""
Tests for Together Culture CRM system.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from .models import Member, Interest, InterestHistory, ActivityLog
from .forms import MemberRegistrationForm, InterestUpdateForm


class InterestModelTest(TestCase):
    """Test Interest model functionality."""
    
    def setUp(self):
        self.interest = Interest.objects.create(
            name='creating',
            description='Creative pursuits and artistic endeavors'
        )
    
    def test_interest_creation(self):
        """Test interest model creation."""
        self.assertEqual(self.interest.name, 'creating')
        self.assertEqual(str(self.interest), 'Creating')
    
    def test_interest_choices(self):
        """Test that only valid interest choices are accepted."""
        valid_choices = ['caring', 'sharing', 'creating', 'experiencing', 'working']
        for choice in valid_choices:
            interest = Interest(name=choice)
            interest.full_clean()  # Should not raise ValidationError


class MemberModelTest(TestCase):
    """Test Member model functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser@example.com',
            email='testuser@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.member = Member.objects.create(
            user=self.user,
            bio='Test bio for user',
            status='pending'
        )
        
        self.interest = Interest.objects.create(name='creating')
    
    def test_member_creation(self):
        """Test member model creation."""
        self.assertEqual(self.member.user, self.user)
        self.assertEqual(self.member.status, 'pending')
        self.assertEqual(self.member.full_name, 'Test User')
        self.assertEqual(self.member.email, 'testuser@example.com')
    
    def test_member_approval(self):
        """Test member approval functionality."""
        self.assertEqual(self.member.status, 'pending')
        self.assertIsNone(self.member.date_approved)
        
        self.member.approve_membership(self.admin_user)
        
        self.assertEqual(self.member.status, 'approved')
        self.assertIsNotNone(self.member.date_approved)
        self.assertEqual(self.member.approved_by, self.admin_user)
    
    def test_member_rejection(self):
        """Test member rejection functionality."""
        self.member.reject_membership()
        self.assertEqual(self.member.status, 'rejected')
    
    def test_member_interests(self):
        """Test member interest functionality."""
        self.member.interests.add(self.interest)
        self.assertIn(self.interest, self.member.interests.all())
        self.assertEqual(self.member.get_interests_list(), ['creating'])


class MemberRegistrationFormTest(TestCase):
    """Test member registration form."""
    
    def setUp(self):
        Interest.objects.create(name='creating')
        Interest.objects.create(name='sharing')
    
    def test_valid_form(self):
        """Test form with valid data."""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': 'strongpassword123',
            'password_confirm': 'strongpassword123',
            'bio': 'Test bio content',
            'interests': [1, 2],
            'terms_accepted': True
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_password_mismatch(self):
        """Test form with mismatched passwords."""
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'password_confirm': 'different123',
            'bio': 'Test bio',
            'interests': [1],
            'terms_accepted': True
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
    
    def test_duplicate_email(self):
        """Test form with existing email."""
        User.objects.create_user(
            username='existing@example.com',
            email='existing@example.com',
            password='pass123'
        )
        
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'existing@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'bio': 'Test bio',
            'interests': [1],
            'terms_accepted': True
        }
        form = MemberRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())


class ViewsTest(TestCase):
    """Test application views."""
    
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.user = User.objects.create_user(
            username='member@example.com',
            email='member@example.com',
            password='memberpass123',
            first_name='Member',
            last_name='User'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        # Create member profile
        self.member = Member.objects.create(
            user=self.user,
            bio='Member bio',
            status='approved'
        )
        
        # Create interests
        self.interest = Interest.objects.create(name='creating')
    
    def test_index_view(self):
        """Test index page loads correctly."""
        response = self.client.get(reverse('crm:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Together Culture')
    
    def test_registration_view_get(self):
        """Test registration page loads."""
        response = self.client.get(reverse('crm:register'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Join Community')
    
    def test_login_view(self):
        """Test login functionality."""
        response = self.client.post(reverse('crm:login'), {
            'email': 'member@example.com',
            'password': 'memberpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_member_dashboard_access(self):
        """Test member dashboard requires login."""
        # Test without login
        response = self.client.get(reverse('crm:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test with login
        self.client.login(username='member@example.com', password='memberpass123')
        response = self.client.get(reverse('crm:dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_admin_dashboard_access(self):
        """Test admin dashboard requires admin privileges."""
        # Test with regular user
        self.client.login(username='member@example.com', password='memberpass123')
        response = self.client.get(reverse('crm:admin_dashboard'))
        self.assertEqual(response.status_code, 302)  # Should redirect
        
        # Test with admin user
        self.client.login(username='admin@example.com', password='adminpass123')
        response = self.client.get(reverse('crm:admin_dashboard'))
        self.assertEqual(response.status_code, 200)
    
    def test_member_search(self):
        """Test member search functionality."""
        self.client.login(username='admin@example.com', password='adminpass123')
        
        response = self.client.get(reverse('crm:member_list'), {
            'search': 'Member'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Member User')


class InterestHistoryTest(TestCase):
    """Test interest history tracking."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='pass123'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True
        )
        
        self.member = Member.objects.create(
            user=self.user,
            bio='Test bio',
            status='approved'
        )
        
        self.interest = Interest.objects.create(name='creating')
    
    def test_interest_history_creation(self):
        """Test that interest history is created."""
        history = InterestHistory.objects.create(
            member=self.member,
            interest=self.interest,
            action='added',
            changed_by=self.admin_user
        )
        
        self.assertEqual(history.member, self.member)
        self.assertEqual(history.interest, self.interest)
        self.assertEqual(history.action, 'added')
        self.assertEqual(history.changed_by, self.admin_user)


class ActivityLogTest(TestCase):
    """Test activity logging."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='pass123'
        )
        
        self.member = Member.objects.create(
            user=self.user,
            bio='Test bio'
        )
    
    def test_activity_log_creation(self):
        """Test activity log creation."""
        log = ActivityLog.objects.create(
            user=self.user,
            action='login',
            description='User logged in',
            ip_address='192.168.1.1'
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.action, 'login')
        self.assertEqual(log.ip_address, '192.168.1.1')