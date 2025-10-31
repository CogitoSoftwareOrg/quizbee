/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3877123827")

  // add field
  collection.fields.addAt(3, new Field({
    "hidden": false,
    "id": "file2366146245",
    "maxSelect": 1,
    "maxSize": 0,
    "mimeTypes": [],
    "name": "cover",
    "presentable": false,
    "protected": false,
    "required": false,
    "system": false,
    "thumbs": [],
    "type": "file"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3877123827")

  // remove field
  collection.fields.removeById("file2366146245")

  return app.save(collection)
})
