/// <reference path="../pb_data/types.d.ts" />

onBootstrap((e) => {
  console.log("Quizbee initialized!");

  //   const meilisearch = require(`${__hooks}/lib/meilisearch.js`).meiliService;
  //   meilisearch.init();

  const tg = require(`${__hooks}/lib/tg.js`).tgService;
  tg.init();

  e.next();
});
