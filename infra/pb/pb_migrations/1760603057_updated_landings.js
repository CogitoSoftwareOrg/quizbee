/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_913459511")

  // add field
  collection.fields.addAt(1, new Field({
    "autogeneratePattern": "",
    "hidden": false,
    "id": "text2560465762",
    "max": 0,
    "min": 0,
    "name": "slug",
    "pattern": "",
    "presentable": false,
    "primaryKey": false,
    "required": false,
    "system": false,
    "type": "text"
  }))

  // add field
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

  // add field
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

  // add field
  collection.fields.addAt(4, new Field({
    "hidden": false,
    "id": "json1862350826",
    "maxSize": 0,
    "name": "structure",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  // add field
  collection.fields.addAt(5, new Field({
    "hidden": false,
    "id": "bool1748787223",
    "name": "published",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "bool"
  }))

  // add field
  collection.fields.addAt(6, new Field({
    "hidden": false,
    "id": "number3206337475",
    "max": null,
    "min": null,
    "name": "version",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_913459511")

  // remove field
  collection.fields.removeById("text2560465762")

  // remove field
  collection.fields.removeById("json4155826103")

  // remove field
  collection.fields.removeById("json1827695573")

  // remove field
  collection.fields.removeById("json1862350826")

  // remove field
  collection.fields.removeById("bool1748787223")

  // remove field
  collection.fields.removeById("number3206337475")

  return app.save(collection)
})
