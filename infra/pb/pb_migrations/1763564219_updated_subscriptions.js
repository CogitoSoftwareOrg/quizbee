/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // add field
  collection.fields.addAt(19, new Field({
    "hidden": false,
    "id": "number3932126314",
    "max": null,
    "min": null,
    "name": "storageLimit",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  // add field
  collection.fields.addAt(20, new Field({
    "hidden": false,
    "id": "number1159907962",
    "max": null,
    "min": null,
    "name": "storageUsage",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // remove field
  collection.fields.removeById("number3932126314")

  // remove field
  collection.fields.removeById("number1159907962")

  return app.save(collection)
})
