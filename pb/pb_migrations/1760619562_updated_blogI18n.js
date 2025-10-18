/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2074964638")

  // add field
  collection.fields.addAt(4, new Field({
    "hidden": false,
    "id": "select1098958488",
    "maxSelect": 1,
    "name": "locale",
    "presentable": false,
    "required": false,
    "system": false,
    "type": "select",
    "values": [
      "en",
      "es",
      "ru",
      "de",
      "fr",
      "pt"
    ]
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2074964638")

  // remove field
  collection.fields.removeById("select1098958488")

  return app.save(collection)
})
