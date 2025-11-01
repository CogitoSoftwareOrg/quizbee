/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_4282183725")

  // add field
  collection.fields.addAt(6, new Field({
    "hidden": false,
    "id": "number2979611598",
    "max": null,
    "min": null,
    "name": "bytes",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  // add field
  collection.fields.addAt(7, new Field({
    "hidden": false,
    "id": "select1002749145",
    "maxSelect": 1,
    "name": "kind",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "select",
    "values": [
      "simple",
      "complex"
    ]
  }))

  // add field
  collection.fields.addAt(8, new Field({
    "hidden": false,
    "id": "file1920773328",
    "maxSelect": 1,
    "maxSize": 0,
    "mimeTypes": [],
    "name": "textFile",
    "presentable": false,
    "protected": false,
    "required": false,
    "system": false,
    "thumbs": [],
    "type": "file"
  }))

  // add field
  collection.fields.addAt(9, new Field({
    "hidden": false,
    "id": "file3760176746",
    "maxSelect": 99,
    "maxSize": 0,
    "mimeTypes": [],
    "name": "images",
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

  // remove field
  collection.fields.removeById("number2979611598")

  // remove field
  collection.fields.removeById("select1002749145")

  // remove field
  collection.fields.removeById("file1920773328")

  // remove field
  collection.fields.removeById("file3760176746")

  return app.save(collection)
})
