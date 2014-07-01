These are the indexes each mongo db should have in order to perform well.
Each section states the collection name and then the indexes. To create an index,
you'll typically either use the mongohq type web interface or a standard terminal console.
If a terminal, this assumes you've logged in and gotten to the mongo prompt 
```
mongo mydatabasename
```

If using the terminal, to add an index to a collection, you'll need to prefix ```ensureIndex``` with
```
db.collection_name
```
as in ```db.location_map.ensureIndex({'course_id': 1}{background: true})```

location_map:
=============

```
ensureIndex({'org': 1, 'offering': 1})
ensureIndex({'schema': 1})
```

fs.files:
=========

Index needed thru 'category' by `_get_all_content_for_course` and others. That query also takes a sort
which can be `uploadDate`, `display_name`, 

Replace existing index which leaves out `run` with this one:
```
ensureIndex({'_id.tag': 1, '_id.org': 1, '_id.course': 1, '_id.category': 1, '_id.run': 1})
ensureIndex({'content_son.tag': 1, 'content_son.org': 1, 'content_son.course': 1, 'content_son.category': 1, 'content_son.run': 1})
```

Note: I'm not advocating adding one which leaves out `category` for now because that would only be
used for `delete_all_course_assets` which in the future should not actually delete the assets except
when doing garbage collection.

Remove index on `displayname`

modulestore:
============

Mongo automatically indexes the ```_id``` field but as a whole. Thus, for queries against modulestore such
as ```modulestore.find({'_id': {'tag': 'i4x', 'org': 'myu', 'course': 'mycourse', 'category': 'problem', 'name': '221abc', 'revision': null}})```
where every field in the id is given in the same order as the field is stored in the record in the db
and no field is omitted.

Because we often query for some subset of the id, we define this index:

```
ensureIndex({'_id.tag': 1, '_id.org': 1, '_id.course': 1, '_id.category': 1, '_id.name': 1, '_id.revision': 1})
```

Because we often scan for all category='course' regardless of the value of the other fields:
```
ensureIndex({'_id.category': 1})
```

Because lms calls get_parent_locations frequently (for path generation):
```
ensureIndex({'_id.tag': 1, '_id.org': 1, '_id.course': 1, 'definition.children': 1})
```

Remove these indices if they exist as I can find no use for them:
```
 { "_id.course": 1, "_id.org": 1, "_id.revision": 1, "definition.children": 1 }
 { "definition.children": 1 }
```

NOTE, that index will only aid queries which provide the keys in exactly that form and order. The query can
omit later fields of the query but not earlier. Thus ```modulestore.find({'_id.org': 'myu'})``` will not use
the index as it omits the tag. As soon as mongo comes across an index field omitted from the query, it stops
considering the index. On the other hand, ```modulestore.find({'_id.tag': 'i4x', '_id.org': 'myu', '_id.category': 'problem'})```
will use the index to get the records matching the tag and org and then will scan all of them
for matches to the category.

To find out if any records have the wrong id structure, run
```
db.fs.files.find({uploadDate: {$gt: startDate, $lt: endDate},
       $where: function() {
           var keys = ['category', 'name', 'course', 'tag', 'org', 'revision'];
           for (var key in this._id) {
               if (key != keys.shift()) {
                   return true;
               }
           }
           return false;
       }},
       {_id: 1})
```

modulestore.active_versions
===========================

```
ensureIndex({'org': 1, 'offering': 1})
```

modulestore.structures
======================

```
ensureIndex({'previous_version': 1})
```

modulestore.definitions
=======================

```
ensureIndex({'category': 1})
```