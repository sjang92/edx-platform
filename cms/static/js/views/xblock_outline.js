define(["jquery", "underscore", "gettext", "js/views/baseview", "js/views/utils/xblock_utils"],
    function($, _, gettext, BaseView, XBlockViewUtils) {

        var XBlockOutlineView = BaseView.extend({
            // takes XBlockInfo as a model

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
                this.addButtonActions(this.$el);
                if (this.shouldRenderChildren()) {
                    listElement = this.$('.sortable-list');
                    children = this.model.get('children');
                    for (i=0; i < children.length; i++) {
                        childOutlineView = this.createChildView(children[i], this.model);
                        childOutlineView.render();
                        listElement.append(childOutlineView.$el);
                    }
                }
                return this;
            },

            addButtonActions: function(element) {
                var self = this;
                element.find('.configure-button').click(function(event) {
                    event.preventDefault();
                    self.editXBlock($(event.target));
                });
                element.find('.delete-button').click(function(event) {
                    event.preventDefault();
                    self.deleteXBlock($(event.target));
                });
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
                    defaultNewChildName = null,
                    html;
                if (childInfo) {
                    addChildName = interpolate(gettext('Add %(component_type)s'), {
                        component_type: childInfo.display_name
                    }, true);
                    defaultNewChildName = interpolate(gettext('New %(component_type)s'), {
                        component_type: childInfo.display_name
                    }, true);
                }
                html = this.template({
                    xblockInfo: xblockInfo,
                    parentInfo: this.parentInfo,
                    xblockType: xblockType,
                    parentType: parentType,
                    childType: childInfo ? this.getXBlockType(childInfo.category, xblockInfo) : null,
                    childCategory: childInfo ? childInfo.category : null,
                    addChildLabel: addChildName,
                    defaultNewChildName: defaultNewChildName,
                    includesChildren: this.shouldRenderChildren()
                });
                if (this.parentInfo) {
                    this.setElement($(html));
                } else {
                    this.$el.html(html);
                }
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

            deleteXBlock: function(target) {
                XBlockViewUtils.deleteXBlock(this.model).done(function() {
                    var item = target.closest('.outline-item');
                    item.remove();
                });
            }
        });

        return XBlockOutlineView;
    }); // end define();
