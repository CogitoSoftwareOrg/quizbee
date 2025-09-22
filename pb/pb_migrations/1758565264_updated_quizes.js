/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // remove field
  collection.fields.removeById("select3144380399")

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // add field
  collection.fields.addAt(6, new Field({
    "hidden": false,
    "id": "select3144380399",
    "maxSelect": 1,
    "name": "difficulty",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "select",
    "values": [
      "beginner",
      "intermediate",
      "expert"
    ]
  }))

  return app.save(collection)
})
