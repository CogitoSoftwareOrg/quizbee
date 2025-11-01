/// <reference path="../pb_data/types.d.ts" />
migrate(
  (app) => {
    const collection = app.findCollectionByNameOrId("pbc_4009210445");

    // add field
    collection.fields.addAt(
      5,
      new Field({
        hidden: false,
        id: "json1355859462",
        maxSize: 0,
        name: "answers",
        presentable: false,
        required: false,
        system: false,
        type: "json",
      })
    );

    return app.save(collection);
  },
  (app) => {
    const collection = app.findCollectionByNameOrId("pbc_4009210445");

    // remove field
    collection.fields.removeById("json1355859462");

    return app.save(collection);
  }
);
