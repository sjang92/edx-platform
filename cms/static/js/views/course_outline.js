define(["jquery", "underscore", "gettext", "js/views/xblock_outline", "js/views/utils/xblock_utils"],
    function($, _, gettext, XBlockOutlineView, XBlockViewUtils) {

        var CourseOutlineView = XBlockOutlineView.extend({
            // takes XBlockInfo as a model

            initialize: function() {
                XBlockOutlineView.prototype.initialize.call(this);
                this.model.on('change', this.onXBlockChange, this);
            },

            onXBlockChange: function() {
                var oldElement = this.$el;
                this.render();
                if (this.parentInfo) {
                    oldElement.replaceWith(this.$el);
                }
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

            addButtonActions: function(element) {
                var self = this;
                XBlockOutlineView.prototype.addButtonActions.call(this, element);
                element.find('.add-button').click(function(event) {
                    event.preventDefault();
                    XBlockViewUtils.addXBlock($(event.target)).done(function(locator) {
                        // TODO: add just the new element (although how will the publish status get propagated?)
                        self.model.fetch();
                    });
                });
            }
        });

        return CourseOutlineView;
    }); // end define();
