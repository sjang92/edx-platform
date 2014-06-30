/**
 * This page is used to show the user an outline of the course.
 */
define(["jquery", "underscore", "gettext", "js/views/pages/base_page", "js/views/utils/xblock_utils",
        "js/views/course_outline"],
    function ($, _, gettext, BasePage, XBlockViewUtils, CourseOutlineView) {
        var CourseOutlinePage = BasePage.extend({
            // takes XBlockInfo as a model

            view: 'container_preview',

            initialize: function() {
                var self = this;
                BasePage.prototype.initialize.call(this);
                this.$('.add-button').click(function(event) {
                    event.preventDefault();
                    XBlockViewUtils.addXBlock($(event.target)).done(function() {
                        self.renderPage();
                    });
                });
            },

            renderPage: function() {
                this.outlineView = new CourseOutlineView({
                    el: this.$('.course-outline'),
                    model: this.model,
                    isRoot: true
                });
                this.outlineView.render();
                return $.Deferred().resolve().promise();
            },

            hasContent: function() {
                return this.model.get('children').length > 0;
            }
        });

        return CourseOutlinePage;
    }); // end define();
