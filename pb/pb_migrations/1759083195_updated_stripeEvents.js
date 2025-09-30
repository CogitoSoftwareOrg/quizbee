/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2737410891")

  // add field
  collection.fields.addAt(2, new Field({
    "hidden": false,
    "id": "json1110206997",
    "maxSize": 0,
    "name": "payload",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2737410891")

  // remove field
  collection.fields.removeById("json1110206997")

  return app.save(collection)
})
