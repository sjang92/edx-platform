define(["jquery", "underscore", "gettext", "js/views/xblock_outline", "js/views/utils/xblock_utils"],
    function($, _, gettext, XBlockOutlineView, XBlockViewUtils) {

        var CourseOutlineView = XBlockOutlineView.extend({
            // takes XBlockInfo as a model

            initialize: function() {
                XBlockOutlineView.prototype.initialize.call(this);
            },

            shouldRenderChildren: function() {
                // Render all nodes up to verticals but not below
                return this.model.get('category') !== 'vertical';
            },

            createChildView: function(xblockInfo, parentInfo) {
                return new CourseOutlineView({
                    model: xblockInfo,
                    parentInfo: parentInfo,
                    template: this.template,
                    parentView: this
                });
            },

            refresh: function() {
                var self = this,
                    url = '/xblock/outline/' + this.model.id;
                this.model.fetch({
                    url: url,
                    success: function() {
                        self.onXBlockChange();
                    }
                });
            },

            addButtonActions: function(element) {
                var self = this;
                XBlockOutlineView.prototype.addButtonActions.call(this, element);
                element.find('.add-button').click(function(event) {
                    event.preventDefault();
                    // TODO: add just the new element rather than refreshing the entire view
                    // (although how will the publish status get propagated?)
                    XBlockViewUtils.addXBlock($(event.target)).done(_.bind(self.refresh, self));
                });
            }
        });

        return CourseOutlineView;
    }); // end define();
