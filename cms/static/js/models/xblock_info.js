define(["backbone", "js/utils/module"], function(Backbone, ModuleUtils) {
    var XBlockInfo = Backbone.Model.extend({

        urlRoot: '/xblock',

        defaults: {
            "id": null,
            "display_name": null,
            "category": null,
            "is_draft": null,
            "is_container": null,
            "data": null,
            "metadata" : null,
            "children": null,
            "studio_url": null,
            "child_info": null,
            "release_date": null
        },

        parse: function(response) {
            var i, rawChildren, children;
            rawChildren = response.children;
            children = [];
            if (rawChildren) {
                for (i=0; i < rawChildren.length; i++) {
                    children.push(this.createChild(rawChildren[i]));
                }
            }
            response.children = children;
            return response;
        },

        createChild: function(response) {
            return new XBlockInfo(response, { parse: true });
        }
    });
    return XBlockInfo;
});
