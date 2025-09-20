/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // update field
  collection.fields.addAt(7, new Field({
    "hidden": false,
    "id": "number696470308",
    "max": null,
    "min": null,
    "name": "quizItemsLimit",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  // update field
  collection.fields.addAt(9, new Field({
    "hidden": false,
    "id": "number2264857908",
    "max": null,
    "min": null,
    "name": "quizItemsUsage",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // update field
  collection.fields.addAt(7, new Field({
    "hidden": false,
    "id": "number696470308",
    "max": null,
    "min": null,
    "name": "quizLimit",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  // update field
  collection.fields.addAt(9, new Field({
    "hidden": false,
    "id": "number2264857908",
    "max": null,
    "min": null,
    "name": "quizUsage",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  return app.save(collection)
})
