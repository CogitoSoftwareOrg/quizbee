/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_2074964638")

  // update collection data
  unmarshal({
    "name": "blogI18n"
  }, collection)

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_2074964638")

  // update collection data
  unmarshal({
    "name": "blog_i18n"
  }, collection)

  return app.save(collection)
})
