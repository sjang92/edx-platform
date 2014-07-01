/**
 * Provides utilities for views to work with xblocks.
 */
define(["jquery", "underscore", "gettext", "js/views/utils/view_utils", "js/utils/module"],
    function($, _, gettext, ViewUtils, ModuleUtils) {
        var addXBlock, deleteXBlock, createUpdateRequestData, updateXBlockField;

        /**
         * Adds an xblock based upon the data attributes of the specified add button. A promise
         * is returned, and the new locator is passed to all done handlers.
         * @param target The add button that was clicked upon.
         * @returns {*} A promise representing the addition of the xblock.
         */
        addXBlock = function(target) {
            var parentLocator = target.data('parent'),
                category = target.data('category'),
                displayName = target.data('default-name');
            return ViewUtils.runOperationShowingMessage(gettext('Adding&hellip;'),
                function() {
                    var addOperation = $.Deferred();
                    analytics.track('Created a ' + category, {
                        'course': course_location_analytics,
                        'display_name': displayName
                    });
                    $.postJSON(ModuleUtils.getUpdateUrl(),
                        {
                            'parent_locator': parentLocator,
                            'category': category,
                            'display_name': displayName
                        }, function(data) {
                            var locator = data.locator;
                            addOperation.resolve(locator);
                        });
                    return addOperation.promise();
                });
        };

        /**
         * Deletes the specified xblock.
         * @param xblockInfo The model for the xblock to be deleted.
         * @returns {*} A promise representing the deletion of the xblock.
         */
        deleteXBlock = function(xblockInfo) {
            var deletion = $.Deferred(),
                url = ModuleUtils.getUpdateUrl(xblockInfo.id);
            ViewUtils.confirmThenRunOperation(gettext('Delete this component?'),
                gettext('Deleting this component is permanent and cannot be undone.'),
                gettext('Yes, delete this component'),
                function() {
                    ViewUtils.runOperationShowingMessage(gettext('Deleting&hellip;'),
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

        createUpdateRequestData = function(fieldName, newValue) {
            var metadata = {};
            metadata[fieldName] = newValue;
            return {
                metadata: metadata
            };
        };

        updateXBlockField = function(xblockInfo, fieldName, newValue) {
            var requestData = createUpdateRequestData(fieldName, newValue);
            ViewUtils.runOperationShowingMessage(gettext('Saving&hellip;'),
                function() {
                    return xblockInfo.save(requestData, { patch: true });
                }).done(function() {
                    // Update the model so that we get the latest publish and last modified information.
                    xblockInfo.fetch();
                });
        };

        return {
            'addXBlock': addXBlock,
            'deleteXBlock': deleteXBlock,
            'updateXBlockField': updateXBlockField
        };
    });
