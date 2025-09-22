/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2000391657")

  // add field
  collection.fields.addAt(3, new Field({
    "hidden": false,
    "id": "json97424953",
    "maxSize": 0,
    "name": "choices",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2000391657")

  // remove field
  collection.fields.removeById("json97424953")

  return app.save(collection)
})
