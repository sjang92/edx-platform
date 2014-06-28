define(["jquery", "underscore", "js/views/xblock_outline"],
    function($, _, XBlockOutlineView) {

        var CourseOutlineView = XBlockOutlineView.extend({
            // takes XBlockInfo as a model

            events : {
                "click .add-button": "addXBlock"
            },

            initialize: function() {
                XBlockOutlineView.prototype.initialize.call(this);
                this.model.on('change', this.onXBlockChange, this);
            },

            onXBlockChange: function() {
                this.render();
            },

            shouldRenderChildren: function() {
                // Render all nodes up to verticals but not below
                return this.model.get('category') !== 'vertical';
            },

            createChildView: function(xblockInfo, parentInfo) {
                return new CourseOutlineView({
                    model: xblockInfo,
                    parentInfo: parentInfo,
                    template: this.template
                });
            },

            addXBlock: function(event) {
                var self = this,
                    target = $(event.target),
                    parentLocator = target.data('parent'),
                    category = target.data('category'),
                    displayName = target.data('default-name');
                if (this.model.id === parentLocator) {
                    event.preventDefault();
                    event.stopPropagation();

                    analytics.track('Created a ' + category, {
                        'course': course_location_analytics,
                        'display_name': displayName
                    });

                    $.postJSON(this.model.urlRoot + '/',
                        {
                            'parent_locator': parentLocator,
                            'category': category,
                            'display_name': displayName
                        },
                        function(data) {
                            var locator = data.locator;
                            window.alert("New locator: " + locator);
                            self.model.fetch();
                        });
                }
            }
        });

        return CourseOutlineView;
    }); // end define();
