# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Handout.
"""

from unittest import skipIf
from ...pages.studio.auto_auth import AutoAuthPage
from ...pages.studio.overview import CourseOutlinePage
from ...pages.studio.video.video import VidoComponentPage
from ...fixtures.course import CourseFixture, XBlockFixtureDesc
from ..helpers import UniqueCourseTest, is_youtube_available


@skipIf(is_youtube_available() is False, 'YouTube is not available!')
class VideoHandoutBaseTest(UniqueCourseTest):

    def setUp(self):
        """
        Initialization of pages and course fixture for tests
        """
        super(VideoHandoutBaseTest, self).setUp()

        self.video = VidoComponentPage(self.browser)

        self.outline = CourseOutlinePage(
            self.browser,
            self.course_info['org'],
            self.course_info['number'],
            self.course_info['run']
        )

        self.course_fixture = CourseFixture(
            self.course_info['org'], self.course_info['number'],
            self.course_info['run'], self.course_info['display_name']
        )

        self.handout = None

    def navigate_to_course_unit(self):
        """
        Install the course with required components and navigate to course unit page
        """
        self._install_course_fixture()
        self._navigate_to_course_unit_page()

    def _install_course_fixture(self):
        """
        Prepare for tests by creating a course with a section, subsection, and unit.
        Performs the following:
            Create a course with a section, subsection, and unit
            Create a user and make that user a course author
            Log the user into studio
        """
        video_metadata = None

        if self.handout:
            self.course_fixture.add_asset([self.handout])
            video_metadata = {'handout': '/static/{handout}'.format(handout=self.handout)}

        # Create course with Video component
        self.course_fixture.add_children(
            XBlockFixtureDesc('chapter', 'Test Section').add_children(
                XBlockFixtureDesc('sequential', 'Test Subsection').add_children(
                    XBlockFixtureDesc("vertical", "Test Unit").add_children(
                        XBlockFixtureDesc('video', 'Video', metadata=video_metadata, publish='make_private'),
                    )
                )
            )
        ).install()

        # Auto login and register the course
        self.auth_page = AutoAuthPage(
            self.browser,
            staff=False,
            username=self.course_fixture.user.get('username'),
            email=self.course_fixture.user.get('email'),
            password=self.course_fixture.user.get('password')
        ).visit()

    def _navigate_to_course_unit_page(self):
        """
        Open the course from the dashboard and expand the section and subsection and click on the Unit link
        The end result is the page where the user is editing the newly created unit
        """
        # Visit Course Outline page
        self.outline.visit()

        # Visit Unit page
        self.outline.section('Test Section').subsection('Test Subsection').toggle_expand().unit('Test Unit').go_to()

        self.video.wait_for_video_component_render()


class VideoHandoutTest(VideoHandoutBaseTest):

    def test_handout_uploads_correctly(self):
        """
        Scenario: Handout uploading works correctly
        Given I have created a Video component with handout file "textbook.pdf"
        Then I can see video button "handout"
        And I can download handout file with mime type "application/pdf"
        """
        self.handout = 'textbook.pdf'

        self.navigate_to_course_unit()

        self.assertTrue(self.video.is_download_handout_button_visible)

        self.assertEqual(self.video.download_handout('application/pdf'), (True, True))
