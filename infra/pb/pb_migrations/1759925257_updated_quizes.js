/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // update collection data
  unmarshal({
    "updateRule": "@request.auth.id = author && @request.body.status:isset = false"
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3109259101")

  // update collection data
  unmarshal({
    "updateRule": "@request.auth.id = author"
  }, collection)

  return app.save(collection)
})
