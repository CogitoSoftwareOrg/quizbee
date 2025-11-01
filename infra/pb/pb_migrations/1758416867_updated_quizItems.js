/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_4009210445")

  // remove field
  collection.fields.removeById("json2390607047")

  // remove field
  collection.fields.removeById("json3777743275")

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_4009210445")

  // add field
  collection.fields.addAt(3, new Field({
    "hidden": false,
    "id": "json2390607047",
    "maxSize": 0,
    "name": "correctAnswer",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  // add field
  collection.fields.addAt(4, new Field({
    "hidden": false,
    "id": "json3777743275",
    "maxSize": 0,
    "name": "wrongAnswers",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "json"
  }))

  return app.save(collection)
})
