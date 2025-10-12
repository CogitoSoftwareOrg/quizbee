/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2000391657")

  // update collection data
  unmarshal({
    "updateRule": "@request.auth.id = user && @request.body.feedback:isset = false"
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2000391657")

  // update collection data
  unmarshal({
    "updateRule": "@request.auth.id = user"
  }, collection)

  return app.save(collection)
})
