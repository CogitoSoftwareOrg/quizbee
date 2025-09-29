/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // add field
  collection.fields.addAt(17, new Field({
    "hidden": false,
    "id": "number2773935344",
    "max": null,
    "min": null,
    "name": "quizesLimit",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  // add field
  collection.fields.addAt(18, new Field({
    "hidden": false,
    "id": "number170611424",
    "max": null,
    "min": null,
    "name": "quizesUsage",
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
  collection.fields.removeById("number2773935344")

  // remove field
  collection.fields.removeById("number170611424")

  return app.save(collection)
})
