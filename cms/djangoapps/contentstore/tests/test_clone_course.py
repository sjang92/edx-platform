from xmodule.modulestore.django import modulestore
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.modulestore import ModuleStoreEnum
from contentstore.tests.utils import CourseTestCase
from xmodule.modulestore.inheritance import own_metadata
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class CloneCourseTest(CourseTestCase):
    def test_clone_course(self):
        # 1. import and populate test toy course
        imported_course = self.import_and_populate_course()

        # 2. clone course (mongo -> mongo)

        # 3. clone course (mongo -> split)

        # 4. clone course (split -> split)


        # now do the actual cloning
        # self.store.clone_course(source_course_id, dest_course_id, self.user.id)


#     def test_portable_link_rewrites_during_clone_course(self):
#         course_data = {
#             'org': 'MITx',
#             'number': '999',
#             'display_name': 'Robot Super Course',
#             'run': '2013_Spring'
#         }
#
#         self.store = modulestore()
#
#         import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
#
#         source_course_id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
#         dest_course_id = _get_course_id(course_data)
#
#         # let's force a non-portable link in the clone source
#         # as a final check, make sure that any non-portable links are rewritten during cloning
#         html_module = self.store.get_item(source_course_id.make_usage_key('html', 'nonportable'))
#
#         self.assertIsInstance(html_module.data, basestring)
#         new_data = html_module.data = html_module.data.replace('/static/', '/c4x/{0}/{1}/asset/'.format(
#             source_course_id.org, source_course_id.run))
#         self.store.update_item(html_module, self.user.id)
#
#         html_module = self.store.get_item(html_module.location)
#         self.assertEqual(new_data, html_module.data)
#
#         # create the destination course
#         _create_course(self, dest_course_id, course_data)
#
#         # do the actual cloning
#         self.store.clone_course(source_course_id, dest_course_id, self.user.id)
#
#         # make sure that any non-portable links are rewritten during cloning
#         html_module = self.store.get_item(dest_course_id.make_usage_key('html', 'nonportable'))
#
#         self.assertIn('/asset/foo.jpg', html_module.data)
#
# def _get_course_id(course_data):
#     """Returns the course ID (org/number/run)."""
#     return SlashSeparatedCourseKey(course_data['org'], course_data['number'], course_data['run'])
