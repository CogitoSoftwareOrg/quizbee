/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // add field
  collection.fields.addAt(13, new Field({
    "hidden": false,
    "id": "json1326724116",
    "maxSize": 0,
    "name": "metadata",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // remove field
  collection.fields.removeById("json1326724116")

  return app.save(collection)
})
