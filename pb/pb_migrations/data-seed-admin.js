/// <reference path="../pb_data/types.d.ts" />
migrate(
  (app) => {
    const email = $os.getenv("PB_EMAIL");
    const password = $os.getenv("PB_PASSWORD");
    const admin = app.findRecordsByFilter(
      "_superusers",
      `email = "${email}"`
    )[0];
    if (!admin) {
      const superusersCol = app.findCollectionByNameOrId("_superusers");
      const admin = new Record(superusersCol);
      admin.set("email", email);
      admin.set("password", password);
      app.save(admin);
    }
  },
  (app) => {
    const email = $os.getenv("PB_EMAIL");
    const admin = app.findRecordsByFilter(
      "_superusers",
      `email = "${email}"`
    )[0];
    if (admin) app.delete(admin);
  }
);
