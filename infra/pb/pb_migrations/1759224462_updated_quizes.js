/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // add field
  collection.fields.addAt(10, new Field({
    "hidden": false,
    "id": "file1172426842",
    "maxSelect": 1,
    "maxSize": 0,
    "mimeTypes": [],
    "name": "materialContext",
    "presentable": false,
    "protected": false,
    "required": false,
    "system": false,
    "thumbs": [],
    "type": "file"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // remove field
  collection.fields.removeById("file1172426842")

  return app.save(collection)
})
