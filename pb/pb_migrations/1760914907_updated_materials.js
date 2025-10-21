/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_4282183725")

  // add field
  collection.fields.addAt(12, new Field({
    "hidden": false,
    "id": "json3280120760",
    "maxSize": 0,
    "name": "trimmedPageRanges",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_4282183725")

  // remove field
  collection.fields.removeById("json3280120760")

  return app.save(collection)
})
