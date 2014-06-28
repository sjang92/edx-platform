/**
 * Provides utilities for views to work with xblocks.
 */
define(["jquery", "underscore", "gettext", "js/views/utils/view_utils"],
    function($, _, gettext, view_utils) {
        var deleteXBlock;

        /**
         *
         * @param xblockElement
         * @returns {*}
         */
        deleteXBlock = function(xblockInfo) {
            var deletion = $.Deferred(),
                url = xblockInfo.urlRoot + '/' + xblockInfo.id;
            view_utils.confirmThenRunOperation(gettext('Delete this component?'),
                gettext('Deleting this component is permanent and cannot be undone.'),
                gettext('Yes, delete this component'),
                function() {
                    view_utils.runOperationShowingMessage(gettext('Deleting&hellip;'),
                        function() {
                            return $.ajax({
                                type: 'DELETE',
                                url: url + "?" + $.param({recurse: true, all_versions: false})
                            }).success(function() {
                                deletion.resolve();
                            });
                        });
                });
            return deletion.promise();
        };

        return {
            'deleteXBlock': deleteXBlock
        };
    });
