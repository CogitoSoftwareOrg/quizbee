/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3980638064")

  // add field
  collection.fields.addAt(2, new Field({
    "autogeneratePattern": "",
    "hidden": false,
    "id": "text106039393",
    "max": 0,
    "min": 0,
    "name": "stripeSubscription",
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
    "id": "date2201122646",
    "max": "",
    "min": "",
    "name": "currentPeriodEnd",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "date"
  }))

  // add field
  collection.fields.addAt(4, new Field({
    "hidden": false,
    "id": "select2063623452",
    "maxSelect": 1,
    "name": "status",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "select",
    "values": [
      "active",
      "incomplete",
      "trialing",
      "past_due",
      "canceled",
      "unpaid"
    ]
  }))

  // add field
  collection.fields.addAt(5, new Field({
    "hidden": false,
    "id": "number3725670697",
    "max": null,
    "min": null,
    "name": "quizesRemained",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  // add field
  collection.fields.addAt(6, new Field({
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

  // add field
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

  // add field
  collection.fields.addAt(8, new Field({
    "hidden": false,
    "id": "number1256664230",
    "max": null,
    "min": null,
    "name": "messageLimit",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  // add field
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

  // add field
  collection.fields.addAt(10, new Field({
    "hidden": false,
    "id": "number3852114614",
    "max": null,
    "min": null,
    "name": "messageUsage",
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
  collection.fields.removeById("text106039393")

  // remove field
  collection.fields.removeById("date2201122646")

  // remove field
  collection.fields.removeById("select2063623452")

  // remove field
  collection.fields.removeById("number3725670697")

  // remove field
  collection.fields.removeById("select242321865")

  // remove field
  collection.fields.removeById("number696470308")

  // remove field
  collection.fields.removeById("number1256664230")

  // remove field
  collection.fields.removeById("number2264857908")

  // remove field
  collection.fields.removeById("number3852114614")

  return app.save(collection)
})
