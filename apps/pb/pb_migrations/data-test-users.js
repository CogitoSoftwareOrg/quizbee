/// <reference path="../pb_data/types.d.ts" />
migrate(
  (app) => {
    const email = "free@gmail.com";
    const password = "breAth20";
    const user = app.findRecordsByFilter("users", `email = "${email}"`)[0];
    if (!user) {
      const usersCol = app.findCollectionByNameOrId("users");
      const user = new Record(usersCol);
      user.set("email", email);
      user.set("password", password);
      user.set("name", "Free User");
      user.set("verified", true);
      app.save(user);
    }
  },
  (app) => {
    const email = "free@gmail.com";
    const user = app.findRecordsByFilter("users", `email = "${email}"`)[0];
    if (user) app.delete(user);
  }
);
