/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // add field
  collection.fields.addAt(2, new Field({
    "cascadeDelete": false,
    "collectionId": "pbc_4282183725",
    "hidden": false,
    "id": "relation2601981621",
    "maxSelect": 999,
    "minSelect": 0,
    "name": "materials",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "relation"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // remove field
  collection.fields.removeById("relation2601981621")

  return app.save(collection)
})
