"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""
import logging
import unittest
from datetime import datetime, timedelta
import pytz

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import RequestFactory, Client
from django.contrib.auth.models import User, AnonymousUser
from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponse
from unittest.case import SkipTest

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from mock import Mock, patch

from student.models import anonymous_id_for_user, user_by_anonymous_id, CourseEnrollment, unique_id_for_user
from student.views import (process_survey_link, _cert_info,
                           change_enrollment, complete_course_mode_info)
from student.tests.factories import UserFactory, CourseModeFactory

import shoppingcart

log = logging.getLogger(__name__)


class CourseEndingTest(TestCase):
    """Test things related to course endings: certificates, surveys, etc"""

    def test_process_survey_link(self):
        username = "fred"
        user = Mock(username=username)
        id = unique_id_for_user(user)
        link1 = "http://www.mysurvey.com"
        self.assertEqual(process_survey_link(link1, user), link1)

        link2 = "http://www.mysurvey.com?unique={UNIQUE_ID}"
        link2_expected = "http://www.mysurvey.com?unique={UNIQUE_ID}".format(UNIQUE_ID=id)
        self.assertEqual(process_survey_link(link2, user), link2_expected)

    def test_cert_info(self):
        user = Mock(username="fred")
        survey_url = "http://a_survey.com"
        course = Mock(end_of_course_survey_url=survey_url)

        self.assertEqual(_cert_info(user, course, None),
                         {'status': 'processing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,
                          })

        cert_status = {'status': 'unavailable'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'processing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,
                          'mode': None
                          })

        cert_status = {'status': 'generating', 'grade': '67', 'mode': 'honor'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'generating',
                          'show_disabled_download_button': True,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67',
                          'mode': 'honor'
                          })

        cert_status = {'status': 'regenerating', 'grade': '67', 'mode': 'verified'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'generating',
                          'show_disabled_download_button': True,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67',
                          'mode': 'verified'
                          })

        download_url = 'http://s3.edx/cert'
        cert_status = {'status': 'downloadable', 'grade': '67',
                       'download_url': download_url, 'mode': 'honor'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'ready',
                          'show_disabled_download_button': False,
                          'show_download_url': True,
                          'download_url': download_url,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67',
                          'mode': 'honor'
                          })

        cert_status = {'status': 'notpassing', 'grade': '67',
                       'download_url': download_url, 'mode': 'honor'}
        self.assertEqual(_cert_info(user, course, cert_status),
                         {'status': 'notpassing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': True,
                          'survey_url': survey_url,
                          'grade': '67',
                          'mode': 'honor'
                          })

        # Test a course that doesn't have a survey specified
        course2 = Mock(end_of_course_survey_url=None)
        cert_status = {'status': 'notpassing', 'grade': '67',
                       'download_url': download_url, 'mode': 'honor'}
        self.assertEqual(_cert_info(user, course2, cert_status),
                         {'status': 'notpassing',
                          'show_disabled_download_button': False,
                          'show_download_url': False,
                          'show_survey_button': False,
                          'grade': '67',
                          'mode': 'honor'
                          })


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class DashboardTest(TestCase):
    """
    Tests for dashboard utility functions
    """
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"
    COURSE_ORG = "EDX"

    def setUp(self):
        self.course = CourseFactory.create(org=self.COURSE_ORG, display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        self.assertIsNotNone(self.course)
        self.user = UserFactory.create(username="jack", email="jack@fake.edx.org", password='test')
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor Code',
        )
        self.client = Client()

    def check_verification_status_on(self, mode, value):
        """
        Check that the css class and the status message are in the dashboard html.
        """
        CourseEnrollment.enroll(self.user, self.course.location.course_key, mode=mode)
        try:
            response = self.client.get(reverse('dashboard'))
        except NoReverseMatch:
            raise SkipTest("Skip this test if url cannot be found (ie running from CMS tests)")
        self.assertContains(response, "class=\"course {0}\"".format(mode))
        self.assertContains(response, value)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_VERIFIED_CERTIFICATES': True})
    def test_verification_status_visible(self):
        """
        Test that the certificate verification status for courses is visible on the dashboard.
        """
        self.client.login(username="jack", password="test")
        self.check_verification_status_on('verified', 'You\'re enrolled as a verified student')
        self.check_verification_status_on('honor', 'You\'re enrolled as an honor code student')
        self.check_verification_status_on('audit', 'You\'re auditing this course')

    def check_verification_status_off(self, mode, value):
        """
        Check that the css class and the status message are not in the dashboard html.
        """
        CourseEnrollment.enroll(self.user, self.course.location.course_key, mode=mode)
        try:
            response = self.client.get(reverse('dashboard'))
        except NoReverseMatch:
            raise SkipTest("Skip this test if url cannot be found (ie running from CMS tests)")
        self.assertNotContains(response, "class=\"course {0}\"".format(mode))
        self.assertNotContains(response, value)

    @patch.dict("django.conf.settings.FEATURES", {'ENABLE_VERIFIED_CERTIFICATES': False})
    def test_verification_status_invisible(self):
        """
        Test that the certificate verification status for courses is not visible on the dashboard
        if the verified certificates setting is off.
        """
        self.client.login(username="jack", password="test")
        self.check_verification_status_off('verified', 'You\'re enrolled as a verified student')
        self.check_verification_status_off('honor', 'You\'re enrolled as an honor code student')
        self.check_verification_status_off('audit', 'You\'re auditing this course')

    def test_course_mode_info(self):
        verified_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        enrollment = CourseEnrollment.enroll(self.user, self.course.id)
        course_mode_info = complete_course_mode_info(self.course.id, enrollment)
        self.assertTrue(course_mode_info['show_upsell'])
        self.assertEquals(course_mode_info['days_for_upsell'], 1)

        verified_mode.expiration_datetime = datetime.now(pytz.UTC) + timedelta(days=-1)
        verified_mode.save()
        course_mode_info = complete_course_mode_info(self.course.id, enrollment)
        self.assertFalse(course_mode_info['show_upsell'])
        self.assertIsNone(course_mode_info['days_for_upsell'])

    def test_refundable(self):
        verified_mode = CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='verified',
            mode_display_name='Verified',
            expiration_datetime=datetime.now(pytz.UTC) + timedelta(days=1)
        )
        enrollment = CourseEnrollment.enroll(self.user, self.course.id, mode='verified')

        self.assertTrue(enrollment.refundable())

        verified_mode.expiration_datetime = datetime.now(pytz.UTC) - timedelta(days=1)
        verified_mode.save()
        self.assertFalse(enrollment.refundable())



class EnrollInCourseTest(TestCase):
    """Tests enrolling and unenrolling in courses."""

    def setUp(self):
        patcher = patch('student.models.tracker')
        self.mock_tracker = patcher.start()
        self.addCleanup(patcher.stop)

    def test_enrollment(self):
        user = User.objects.create_user("joe", "joe@joe.com", "password")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")
        course_id_partial = SlashSeparatedCourseKey("edX", "Test101", None)

        # Test basic enrollment
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assertTrue(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        self.assert_enrollment_event_was_emitted(user, course_id)

        # Enrolling them again should be harmless
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assertTrue(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        self.assert_no_events_were_emitted()

        # Now unenroll the user
        CourseEnrollment.unenroll(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        self.assert_unenrollment_event_was_emitted(user, course_id)

        # Unenrolling them again should also be harmless
        CourseEnrollment.unenroll(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assertFalse(CourseEnrollment.is_enrolled_by_partial(user, course_id_partial))
        self.assert_no_events_were_emitted()

        # The enrollment record should still exist, just be inactive
        enrollment_record = CourseEnrollment.objects.get(
            user=user,
            course_id=course_id
        )
        self.assertFalse(enrollment_record.is_active)

        # Make sure mode is updated properly if user unenrolls & re-enrolls
        enrollment = CourseEnrollment.enroll(user, course_id, "verified")
        self.assertEquals(enrollment.mode, "verified")
        CourseEnrollment.unenroll(user, course_id)
        enrollment = CourseEnrollment.enroll(user, course_id, "audit")
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assertEquals(enrollment.mode, "audit")

    def assert_no_events_were_emitted(self):
        """Ensures no events were emitted since the last event related assertion"""
        self.assertFalse(self.mock_tracker.emit.called)  # pylint: disable=maybe-no-member
        self.mock_tracker.reset_mock()


    def assert_enrollment_mode_change_event_was_emitted(self, user, course_key, mode):
        self.mock_tracker.emit.assert_called_once_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.mode_changed',
            {
                'course_id': course_key.to_deprecated_string(),
                'user_id': user.pk,
                'mode': mode
            }
        )
        self.mock_tracker.reset_mock()

    def assert_enrollment_event_was_emitted(self, user, course_key):
        """Ensures an enrollment event was emitted since the last event related assertion"""
        self.mock_tracker.emit.assert_called_once_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.activated',
            {
                'course_id': course_key.to_deprecated_string(),
                'user_id': user.pk,
                'mode': 'honor'
            }
        )
        self.mock_tracker.reset_mock()

    def assert_unenrollment_event_was_emitted(self, user, course_key):
        """Ensures an unenrollment event was emitted since the last event related assertion"""
        self.mock_tracker.emit.assert_called_once_with(  # pylint: disable=maybe-no-member
            'edx.course.enrollment.deactivated',
            {
                'course_id': course_key.to_deprecated_string(),
                'user_id': user.pk,
                'mode': 'honor'
            }
        )
        self.mock_tracker.reset_mock()

    def test_enrollment_non_existent_user(self):
        # Testing enrollment of newly unsaved user (i.e. no database entry)
        user = User(username="rusty", email="rusty@fake.edx.org")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")

        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Unenroll does nothing
        CourseEnrollment.unenroll(user, course_id)
        self.assert_no_events_were_emitted()

        # Implicit save() happens on new User object when enrolling, so this
        # should still work
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)

    def test_enrollment_by_email(self):
        user = User.objects.create(username="jack", email="jack@fake.edx.org")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")

        CourseEnrollment.enroll_by_email("jack@fake.edx.org", course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)

        # This won't throw an exception, even though the user is not found
        self.assertIsNone(
            CourseEnrollment.enroll_by_email("not_jack@fake.edx.org", course_id)
        )
        self.assert_no_events_were_emitted()

        self.assertRaises(
            User.DoesNotExist,
            CourseEnrollment.enroll_by_email,
            "not_jack@fake.edx.org",
            course_id,
            ignore_errors=False
        )
        self.assert_no_events_were_emitted()

        # Now unenroll them by email
        CourseEnrollment.unenroll_by_email("jack@fake.edx.org", course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_unenrollment_event_was_emitted(user, course_id)

        # Harmless second unenroll
        CourseEnrollment.unenroll_by_email("jack@fake.edx.org", course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_no_events_were_emitted()

        # Unenroll on non-existent user shouldn't throw an error
        CourseEnrollment.unenroll_by_email("not_jack@fake.edx.org", course_id)
        self.assert_no_events_were_emitted()

    def test_enrollment_multiple_classes(self):
        user = User(username="rusty", email="rusty@fake.edx.org")
        course_id1 = SlashSeparatedCourseKey("edX", "Test101", "2013")
        course_id2 = SlashSeparatedCourseKey("MITx", "6.003z", "2012")

        CourseEnrollment.enroll(user, course_id1)
        self.assert_enrollment_event_was_emitted(user, course_id1)
        CourseEnrollment.enroll(user, course_id2)
        self.assert_enrollment_event_was_emitted(user, course_id2)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id2))

        CourseEnrollment.unenroll(user, course_id1)
        self.assert_unenrollment_event_was_emitted(user, course_id1)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id2))

        CourseEnrollment.unenroll(user, course_id2)
        self.assert_unenrollment_event_was_emitted(user, course_id2)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id1))
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id2))

    def test_activation(self):
        user = User.objects.create(username="jack", email="jack@fake.edx.org")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))

        # Creating an enrollment doesn't actually enroll a student
        # (calling CourseEnrollment.enroll() would have)
        enrollment = CourseEnrollment.get_or_create_enrollment(user, course_id)
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_no_events_were_emitted()

        # Until you explicitly activate it
        enrollment.activate()
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)

        # Activating something that's already active does nothing
        enrollment.activate()
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_no_events_were_emitted()

        # Now deactive
        enrollment.deactivate()
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_unenrollment_event_was_emitted(user, course_id)

        # Deactivating something that's already inactive does nothing
        enrollment.deactivate()
        self.assertFalse(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_no_events_were_emitted()

        # A deactivated enrollment should be activated if enroll() is called
        # for that user/course_id combination
        CourseEnrollment.enroll(user, course_id)
        self.assertTrue(CourseEnrollment.is_enrolled(user, course_id))
        self.assert_enrollment_event_was_emitted(user, course_id)


    def test_change_enrollment_modes(self):
        user = User.objects.create(username="justin", email="jh@fake.edx.org")
        course_id = SlashSeparatedCourseKey("edX", "Test101", "2013")

        CourseEnrollment.enroll(user, course_id)
        self.assert_enrollment_event_was_emitted(user, course_id)

        CourseEnrollment.enroll(user, course_id,"audit")
        self.assert_enrollment_mode_change_event_was_emitted(user, course_id, "audit")

        # same enrollment mode does not emit an event
        CourseEnrollment.enroll(user, course_id,"audit")
        self.assert_no_events_were_emitted()

        CourseEnrollment.enroll(user, course_id,"honor")
        self.assert_enrollment_mode_change_event_was_emitted(user, course_id, "honor")


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class PaidRegistrationTest(ModuleStoreTestCase):
    """
    Tests for paid registration functionality (not verified student), involves shoppingcart
    """
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"
    COURSE_ORG = "EDX"

    def setUp(self):
        # Create course
        self.req_factory = RequestFactory()
        self.course = CourseFactory.create(org=self.COURSE_ORG, display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        self.assertIsNotNone(self.course)
        self.user = User.objects.create(username="jack", email="jack@fake.edx.org")

    @unittest.skipUnless(settings.FEATURES.get('ENABLE_SHOPPING_CART'), "Shopping Cart not enabled in settings")
    def test_change_enrollment_add_to_cart(self):
        request = self.req_factory.post(reverse('change_enrollment'), {'course_id': self.course.id.to_deprecated_string(),
                                                                       'enrollment_action': 'add_to_cart'})
        request.user = self.user
        response = change_enrollment(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, reverse('shoppingcart.views.show_cart'))
        self.assertTrue(shoppingcart.models.PaidCourseRegistration.contained_in_order(
            shoppingcart.models.Order.get_cart_for_user(self.user), self.course.id))


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AnonymousLookupTable(TestCase):
    """
    Tests for anonymous_id_functions
    """
    # arbitrary constant
    COURSE_SLUG = "100"
    COURSE_NAME = "test_course"
    COURSE_ORG = "EDX"

    def setUp(self):
        self.course = CourseFactory.create(org=self.COURSE_ORG, display_name=self.COURSE_NAME, number=self.COURSE_SLUG)
        self.assertIsNotNone(self.course)
        self.user = UserFactory()
        CourseModeFactory.create(
            course_id=self.course.id,
            mode_slug='honor',
            mode_display_name='Honor Code',
        )
        patcher = patch('student.models.tracker')
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_for_unregistered_user(self):  # same path as for logged out user
        self.assertEqual(None, anonymous_id_for_user(AnonymousUser(), self.course.id))
        self.assertIsNone(user_by_anonymous_id(None))

    def test_roundtrip_for_logged_user(self):
        enrollment = CourseEnrollment.enroll(self.user, self.course.id)
        anonymous_id = anonymous_id_for_user(self.user, self.course.id)
        real_user = user_by_anonymous_id(anonymous_id)
        self.assertEqual(self.user, real_user)
        self.assertEqual(anonymous_id, anonymous_id_for_user(self.user, self.course.id, save=False))
