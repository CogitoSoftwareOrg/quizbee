/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // update field
  collection.fields.addAt(4, new Field({
    "hidden": false,
    "id": "number725808004",
    "max": null,
    "min": null,
    "name": "itemsLimit",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // update field
  collection.fields.addAt(4, new Field({
    "hidden": false,
    "id": "number725808004",
    "max": null,
    "min": null,
    "name": "itemLimit",
    "onlyInt": false,
    "presentable": false,
    "required": false,
    "system": false,
    "type": "number"
  }))

  return app.save(collection)
})
