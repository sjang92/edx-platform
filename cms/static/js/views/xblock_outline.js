define(["jquery", "underscore", "gettext", "js/views/baseview", "js/views/utils/xblock_utils"],
    function($, _, gettext, BaseView, xblock_utils) {

        var XBlockOutlineView = BaseView.extend({
            // takes XBlockInfo as a model

            events : {
                "click .delete-button": "deleteXBlock"
            },

            initialize: function() {
                BaseView.prototype.initialize.call(this);
                this.template = this.options.template;
                if (!this.template) {
                    this.template = this.loadTemplate('xblock-outline');
                }
                this.parentInfo = this.options.parentInfo;
            },

            render: function() {
                var i, children, listElement, childOutlineView;
                this.renderTemplate();
                if (this.shouldRenderChildren()) {
                    listElement = this.$('.sortable-list');
                    children = this.model.get('children');
                    for (i=0; i < children.length; i++) {
                        childOutlineView = this.createChildView(children[i], this.model);
                        childOutlineView.render();
                        listElement.append(childOutlineView.$('li').first());
                    }
                }
                return this;
            },

            shouldRenderChildren: function() {
                return true;
            },

            createChildView: function(xblockInfo, parentInfo) {
                return new XBlockOutlineView({
                    model: xblockInfo,
                    parentInfo: parentInfo,
                    template: this.template
                });
            },

            renderTemplate: function() {
                var xblockInfo = this.model,
                    childInfo = xblockInfo.get('child_info'),
                    parentInfo = this.parentInfo,
                    xblockType = this.getXBlockType(this.model.get('category'), this.parentInfo),
                    parentType = parentInfo ? this.getXBlockType(parentInfo.get('category')) : null,
                    addChildName = null,
                    defaultNewChildName = null;
                if (childInfo) {
                    addChildName = interpolate(gettext('Add %(component_type)s'), {
                        component_type: childInfo.display_name
                    }, true);
                    defaultNewChildName = interpolate(gettext('New %(component_type)s'), {
                        component_type: childInfo.display_name
                    }, true);
                }
                this.$el.html(this.template({
                    xblockInfo: xblockInfo,
                    parentInfo: this.parentInfo,
                    xblockType: xblockType,
                    parentType: parentType,
                    childType: childInfo ? this.getXBlockType(childInfo.category, xblockInfo) : null,
                    childCategory: childInfo ? childInfo.category : null,
                    addChildLabel: addChildName,
                    defaultNewChildName: defaultNewChildName,
                    includesChildren: this.shouldRenderChildren()
                }));
            },

            getXBlockType: function(category, parentInfo) {
                var xblockType = category;
                if (category === 'chapter') {
                    xblockType = 'section';
                } else if (category === 'sequential') {
                    xblockType = 'subsection';
                } else if (category === 'vertical' && parentInfo && parentInfo.get('category') === 'sequential') {
                    xblockType = 'unit';
                }
                return xblockType;
            },

            deleteXBlock: function(event) {
                event.preventDefault();
                xblock_utils.deleteXBlock(this.model).done(function() {
                    window.alert("Deleted xblock!");
                });
            }
        });

        return XBlockOutlineView;
    }); // end define();
