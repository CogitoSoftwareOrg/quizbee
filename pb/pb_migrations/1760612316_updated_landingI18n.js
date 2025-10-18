/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_996352553")

  // update collection data
  unmarshal({
    "name": "landingsI18n"
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_996352553")

  // update collection data
  unmarshal({
    "name": "landingI18n"
  }, collection)

  return app.save(collection)
})
