/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_4282183725")

  // update field
  collection.fields.addAt(8, new Field({
    "hidden": false,
    "id": "file1920773328",
    "maxSelect": 1,
    "maxSize": 5000000,
    "mimeTypes": [],
    "name": "textFile",
    "presentable": false,
    "protected": false,
    "required": false,
    "system": false,
    "thumbs": [],
    "type": "file"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_4282183725")

  // update field
  collection.fields.addAt(8, new Field({
    "hidden": false,
    "id": "file1920773328",
    "maxSelect": 1,
    "maxSize": 10,
    "mimeTypes": [],
    "name": "textFile",
    "presentable": false,
    "protected": false,
    "required": false,
    "system": false,
    "thumbs": [],
    "type": "file"
  }))

  return app.save(collection)
})
