/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_4009210445")

  // update collection data
  unmarshal({
    "name": "quizItems"
  }, collection)

  // add field
  collection.fields.addAt(2, new Field({
    "autogeneratePattern": "",
    "hidden": false,
    "id": "text3069659470",
    "max": 0,
    "min": 0,
    "name": "question",
    "pattern": "",
    "presentable": false,
    "primaryKey": false,
    "required": false,
    "system": false,
    "type": "text"
  }))

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
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_4009210445")

  // update collection data
  unmarshal({
    "name": "questions"
  }, collection)

  // remove field
  collection.fields.removeById("text3069659470")

  // remove field
  collection.fields.removeById("json2390607047")

  // remove field
  collection.fields.removeById("json3777743275")

  return app.save(collection)
})
