/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // update collection data
  unmarshal({
    "listRule": "@request.auth.id = author || visibility = 'search'",
    "viewRule": "@request.auth.id = author || visibility != 'private'"
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // update collection data
  unmarshal({
    "listRule": "@request.auth.id = author",
    "viewRule": "@request.auth.id = author"
  }, collection)

  return app.save(collection)
})
