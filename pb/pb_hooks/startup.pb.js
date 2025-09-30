/// <reference path="../pb_data/types.d.ts" />

onBootstrap((e) => {
  console.log("Quizbee initialized!");

  //   const meilisearch = require(`${__hooks}/lib/meilisearch.js`).meiliService;
  //   meilisearch.init();

  e.next();
});
