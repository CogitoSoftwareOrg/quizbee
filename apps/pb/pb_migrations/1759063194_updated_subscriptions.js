/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // add field
  collection.fields.addAt(13, new Field({
    "hidden": false,
    "id": "date4294391523",
    "max": "",
    "min": "",
    "name": "currentPeriodStart",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "date"
  }))

  // add field
  collection.fields.addAt(14, new Field({
    "hidden": false,
    "id": "bool556524030",
    "name": "cancelAtPeriodEnd",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "bool"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // remove field
  collection.fields.removeById("date4294391523")

  // remove field
  collection.fields.removeById("bool556524030")

  return app.save(collection)
})
