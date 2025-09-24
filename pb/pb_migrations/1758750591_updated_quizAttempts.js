/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2000391657")

  // add field
  collection.fields.addAt(4, new Field({
    "hidden": false,
    "id": "json3525919832",
    "maxSize": 0,
    "name": "feedback",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2000391657")

  // remove field
  collection.fields.removeById("json3525919832")

  return app.save(collection)
})
