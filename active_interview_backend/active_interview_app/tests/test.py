from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from active_interview_app.models import InterviewTemplate, UserProfile

# from django.core import mail


class LoginTest(TestCase):
    def testregister(self):
        register = User.objects.create_user(username='craig', password='1')
        self.assertTrue(register != None)

    def testlogin(self):
        User.objects.create_user(username='craig', password='1')
        login = self.client.login(username='craig', password='1')

        self.assertTrue(login)

    def testlogout(self):
        User.objects.create_user(username='craig', password='1')
        self.client.login(username='craig', password='1')
        logout = self.client.logout()
        self.assertTrue(logout == None)

    def testfaillogin(self):
        User.objects.create_user(username='craig', password='1')
        login = self.client.login(username='craig', password='2')
        self.assertFalse(login)


class TestFeaturesPage(TestCase):
    def testGETFeaturesPage(self):
        # Call the view with a response
        response = self.client.get(reverse('features'))

        # Validate that the view is valid
        self.assertEqual(response.status_code, 200)

        # Validate that the index template was used
        self.assertTemplateUsed(response, 'base.html')


class InterviewTemplateSectionTests(TestCase):
    """
    Test cases for Interview Template section management with weights.
    Tests adding, editing, and deleting sections with weight values.
    """

    def setUp(self):
        """Set up test user and template"""
        # Create interviewer user
        self.user = User.objects.create_user(
            username='interviewer1',
            password='testpass123'
        )
        self.user.profile.role = UserProfile.INTERVIEWER
        self.user.profile.save()

        # Create template
        self.template = InterviewTemplate.objects.create(
            name='Technical Interview',
            description='Test template',
            user=self.user
        )

        # Login
        self.client.login(username='interviewer1', password='testpass123')

    def test_add_section_with_weight(self):
        """Test adding a section with a weight value"""
        response = self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {
                'title': 'Technical Skills',
                'content': 'Assess technical competencies',
                'weight': 40
            }
        )

        # Should redirect to template detail
        self.assertEqual(response.status_code, 302)

        # Reload template from database
        self.template.refresh_from_db()

        # Verify section was added
        self.assertEqual(len(self.template.sections), 1)
        section = self.template.sections[0]
        self.assertEqual(section['title'], 'Technical Skills')
        self.assertEqual(section['content'], 'Assess technical competencies')
        self.assertEqual(section['weight'], 40)
        self.assertEqual(section['order'], 0)
        self.assertIn('id', section)

    def test_add_multiple_sections_with_different_weights(self):
        """Test adding multiple sections with different weights"""
        # Add first section
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Technical Skills', 'content': 'Test 1', 'weight': 30}
        )

        # Add second section
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Experience', 'content': 'Test 2', 'weight': 25}
        )

        # Add third section
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Education', 'content': 'Test 3', 'weight': 20}
        )

        # Reload template
        self.template.refresh_from_db()

        # Verify all sections
        self.assertEqual(len(self.template.sections), 3)
        self.assertEqual(self.template.sections[0]['weight'], 30)
        self.assertEqual(self.template.sections[1]['weight'], 25)
        self.assertEqual(self.template.sections[2]['weight'], 20)

    def test_edit_section_weight(self):
        """Test editing a section's weight"""
        # Add a section first
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Original Title', 'content': 'Original content', 'weight': 10}
        )

        self.template.refresh_from_db()
        section_id = self.template.sections[0]['id']

        # Edit the section
        response = self.client.post(
            reverse('edit_section', kwargs={
                'template_id': self.template.id,
                'section_id': section_id
            }),
            {
                'title': 'Updated Title',
                'content': 'Updated content',
                'weight': 35
            }
        )

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Reload and verify changes
        self.template.refresh_from_db()
        section = self.template.sections[0]
        self.assertEqual(section['title'], 'Updated Title')
        self.assertEqual(section['content'], 'Updated content')
        self.assertEqual(section['weight'], 35)

    def test_delete_section(self):
        """Test deleting a section"""
        # Add two sections
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 1', 'content': 'Content 1', 'weight': 10}
        )
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 2', 'content': 'Content 2', 'weight': 20}
        )

        self.template.refresh_from_db()
        self.assertEqual(len(self.template.sections), 2)

        section_id = self.template.sections[0]['id']

        # Delete first section
        response = self.client.post(
            reverse('delete_section', kwargs={
                'template_id': self.template.id,
                'section_id': section_id
            })
        )

        # Should redirect
        self.assertEqual(response.status_code, 302)

        # Reload and verify
        self.template.refresh_from_db()
        self.assertEqual(len(self.template.sections), 1)
        self.assertEqual(self.template.sections[0]['title'], 'Section 2')
        # Order should be reindexed
        self.assertEqual(self.template.sections[0]['order'], 0)

    def test_add_section_without_title_fails(self):
        """Test that adding a section without title fails"""
        response = self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {
                'title': '',
                'content': 'Some content',
                'weight': 10
            }
        )

        # Should redirect back
        self.assertEqual(response.status_code, 302)

        # Reload template - should have no sections
        self.template.refresh_from_db()
        self.assertEqual(len(self.template.sections), 0)

    def test_add_section_with_negative_weight_fails(self):
        """Test that negative weight values are rejected"""
        response = self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {
                'title': 'Test Section',
                'content': 'Test content',
                'weight': -10
            }
        )

        # Should redirect back
        self.assertEqual(response.status_code, 302)

        # Reload template - should have no sections
        self.template.refresh_from_db()
        self.assertEqual(len(self.template.sections), 0)

    def test_add_section_with_invalid_weight_fails(self):
        """Test that non-numeric weight values are rejected"""
        response = self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {
                'title': 'Test Section',
                'content': 'Test content',
                'weight': 'invalid'
            }
        )

        # Should redirect back
        self.assertEqual(response.status_code, 302)

        # Reload template - should have no sections
        self.template.refresh_from_db()
        self.assertEqual(len(self.template.sections), 0)

    def test_candidate_cannot_add_section(self):
        """Test that candidates cannot add sections to templates"""
        # Create candidate user
        candidate = User.objects.create_user(
            username='candidate1',
            password='testpass123'
        )
        candidate.profile.role = UserProfile.CANDIDATE
        candidate.profile.save()

        # Login as candidate
        self.client.login(username='candidate1', password='testpass123')

        # Try to add section
        response = self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {
                'title': 'Test Section',
                'content': 'Test content',
                'weight': 10
            }
        )

        # Should be forbidden
        self.assertEqual(response.status_code, 403)

    def test_section_weight_zero_is_valid(self):
        """Test that zero weight is valid"""
        response = self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {
                'title': 'Optional Section',
                'content': 'This has zero weight',
                'weight': 0
            }
        )

        # Should redirect successfully
        self.assertEqual(response.status_code, 302)

        # Reload and verify
        self.template.refresh_from_db()
        self.assertEqual(len(self.template.sections), 1)
        self.assertEqual(self.template.sections[0]['weight'], 0)

    def test_total_weight_cannot_exceed_100_percent(self):
        """Test that adding a section that would exceed 100% total weight is rejected"""
        # Add first section with 60% weight
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 1', 'content': 'Content 1', 'weight': 60}
        )

        # Try to add second section with 50% weight (would total 110%)
        response = self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {
                'title': 'Section 2',
                'content': 'Content 2',
                'weight': 50
            }
        )

        # Should redirect back
        self.assertEqual(response.status_code, 302)

        # Reload template - should still only have 1 section
        self.template.refresh_from_db()
        self.assertEqual(len(self.template.sections), 1)
        self.assertEqual(self.template.sections[0]['weight'], 60)

    def test_total_weight_exactly_100_percent_is_valid(self):
        """Test that adding sections totaling exactly 100% is valid"""
        # Add sections totaling 100%
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 1', 'content': 'Content 1', 'weight': 40}
        )
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 2', 'content': 'Content 2', 'weight': 35}
        )
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 3', 'content': 'Content 3', 'weight': 25}
        )

        # Reload and verify
        self.template.refresh_from_db()
        self.assertEqual(len(self.template.sections), 3)

        # Calculate total
        total = sum(s['weight'] for s in self.template.sections)
        self.assertEqual(total, 100)

    def test_edit_section_weight_cannot_exceed_100_percent(self):
        """Test that editing a section weight that would exceed 100% is rejected"""
        # Add two sections: 40% and 30%
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 1', 'content': 'Content 1', 'weight': 40}
        )
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 2', 'content': 'Content 2', 'weight': 30}
        )

        self.template.refresh_from_db()
        section_id = self.template.sections[0]['id']

        # Try to edit first section to 80% (would total 110% with second section)
        response = self.client.post(
            reverse('edit_section', kwargs={
                'template_id': self.template.id,
                'section_id': section_id
            }),
            {
                'title': 'Section 1',
                'content': 'Content 1',
                'weight': 80
            }
        )

        # Should redirect back
        self.assertEqual(response.status_code, 302)

        # Reload and verify weight unchanged
        self.template.refresh_from_db()
        self.assertEqual(self.template.sections[0]['weight'], 40)

    def test_edit_section_weight_to_make_total_100_percent(self):
        """Test that editing a section to make total exactly 100% is valid"""
        # Add two sections: 40% and 30%
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 1', 'content': 'Content 1', 'weight': 40}
        )
        self.client.post(
            reverse('add_section', kwargs={'template_id': self.template.id}),
            {'title': 'Section 2', 'content': 'Content 2', 'weight': 30}
        )

        self.template.refresh_from_db()
        section_id = self.template.sections[1]['id']

        # Edit second section to 60% (making total exactly 100%)
        response = self.client.post(
            reverse('edit_section', kwargs={
                'template_id': self.template.id,
                'section_id': section_id
            }),
            {
                'title': 'Section 2',
                'content': 'Content 2',
                'weight': 60
            }
        )

        # Should succeed
        self.assertEqual(response.status_code, 302)

        # Reload and verify
        self.template.refresh_from_db()
        total = sum(s['weight'] for s in self.template.sections)
        self.assertEqual(total, 100)
        self.assertEqual(self.template.sections[1]['weight'], 60)


class InterviewTemplateModelTests(TestCase):
    """
    Test cases for InterviewTemplate model methods, especially
    weight calculation and status display methods.
    """

    def setUp(self):
        """Set up test user and template"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.template = InterviewTemplate.objects.create(
            name='Test Template',
            description='Test description',
            user=self.user
        )

    def test_get_total_weight_empty_template(self):
        """Test get_total_weight returns 0 for template with no sections"""
        self.assertEqual(self.template.get_total_weight(), 0)

    def test_get_total_weight_with_sections(self):
        """Test get_total_weight calculates correctly with sections"""
        self.template.sections = [
            {'id': '1', 'title': 'Section 1', 'content': 'Content', 'order': 0, 'weight': 30},
            {'id': '2', 'title': 'Section 2', 'content': 'Content', 'order': 1, 'weight': 40},
            {'id': '3', 'title': 'Section 3', 'content': 'Content', 'order': 2, 'weight': 20}
        ]
        self.template.save()
        self.assertEqual(self.template.get_total_weight(), 90)

    def test_get_total_weight_exactly_100(self):
        """Test get_total_weight with sections totaling 100"""
        self.template.sections = [
            {'id': '1', 'title': 'Section 1', 'content': 'Content', 'order': 0, 'weight': 50},
            {'id': '2', 'title': 'Section 2', 'content': 'Content', 'order': 1, 'weight': 50}
        ]
        self.template.save()
        self.assertEqual(self.template.get_total_weight(), 100)

    def test_is_complete_false_when_empty(self):
        """Test is_complete returns False for template with no sections"""
        self.assertFalse(self.template.is_complete())

    def test_is_complete_false_when_under_100(self):
        """Test is_complete returns False when total weight is under 100"""
        self.template.sections = [
            {'id': '1', 'title': 'Section 1', 'content': 'Content', 'order': 0, 'weight': 60}
        ]
        self.template.save()
        self.assertFalse(self.template.is_complete())

    def test_is_complete_true_when_exactly_100(self):
        """Test is_complete returns True when total weight is exactly 100"""
        self.template.sections = [
            {'id': '1', 'title': 'Section 1', 'content': 'Content', 'order': 0, 'weight': 40},
            {'id': '2', 'title': 'Section 2', 'content': 'Content', 'order': 1, 'weight': 35},
            {'id': '3', 'title': 'Section 3', 'content': 'Content', 'order': 2, 'weight': 25}
        ]
        self.template.save()
        self.assertTrue(self.template.is_complete())

    def test_is_complete_false_when_over_100(self):
        """Test is_complete returns False when total weight exceeds 100"""
        self.template.sections = [
            {'id': '1', 'title': 'Section 1', 'content': 'Content', 'order': 0, 'weight': 60},
            {'id': '2', 'title': 'Section 2', 'content': 'Content', 'order': 1, 'weight': 50}
        ]
        self.template.save()
        self.assertFalse(self.template.is_complete())

    def test_get_status_display_wip_when_incomplete(self):
        """Test get_status_display returns 'WIP' for incomplete templates"""
        self.template.sections = [
            {'id': '1', 'title': 'Section 1', 'content': 'Content', 'order': 0, 'weight': 50}
        ]
        self.template.save()
        self.assertEqual(self.template.get_status_display(), 'WIP')

    def test_get_status_display_complete_when_100(self):
        """Test get_status_display returns 'Complete' when total weight is 100"""
        self.template.sections = [
            {'id': '1', 'title': 'Section 1', 'content': 'Content', 'order': 0, 'weight': 100}
        ]
        self.template.save()
        self.assertEqual(self.template.get_status_display(), 'Complete')

    def test_get_status_display_wip_when_empty(self):
        """Test get_status_display returns 'WIP' for empty templates"""
        self.assertEqual(self.template.get_status_display(), 'WIP')

    def test_get_status_display_wip_when_over_100(self):
        """Test get_status_display returns 'WIP' even when over 100% (edge case)"""
        self.template.sections = [
            {'id': '1', 'title': 'Section 1', 'content': 'Content', 'order': 0, 'weight': 110}
        ]
        self.template.save()
        self.assertEqual(self.template.get_status_display(), 'WIP')