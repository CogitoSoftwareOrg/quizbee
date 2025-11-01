/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // update field
  collection.fields.addAt(5, new Field({
    "hidden": false,
    "id": "select242321865",
    "maxSelect": 1,
    "name": "tarif",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "select",
    "values": [
      "plus",
      "pro",
      "free"
    ]
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // update field
  collection.fields.addAt(5, new Field({
    "hidden": false,
    "id": "select242321865",
    "maxSelect": 1,
    "name": "tarif",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "select",
    "values": [
      "plus",
      "pro"
    ]
  }))

  return app.save(collection)
})
