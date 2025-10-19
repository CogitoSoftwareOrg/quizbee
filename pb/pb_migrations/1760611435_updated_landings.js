/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_913459511")

  // update field
  collection.fields.addAt(2, new Field({
    "hidden": false,
    "id": "json4155826103",
    "maxSize": 0,
    "name": "metaCommon",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  // update field
  collection.fields.addAt(3, new Field({
    "hidden": false,
    "id": "json1827695573",
    "maxSize": 0,
    "name": "metaI18n",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_913459511")

  // update field
  collection.fields.addAt(2, new Field({
    "hidden": false,
    "id": "json4155826103",
    "maxSize": 0,
    "name": "meta_common",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  // update field
  collection.fields.addAt(3, new Field({
    "hidden": false,
    "id": "json1827695573",
    "maxSize": 0,
    "name": "meta_i18n",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  return app.save(collection)
})
