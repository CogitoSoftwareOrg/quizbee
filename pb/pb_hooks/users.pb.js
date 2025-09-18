onRecordCreate((e) => {
  // before creation

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after creation
}, "users");

onRecordUpdate((e) => {
  // before update

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after update
}, "users");

onRecordDelete((e) => {
  // before deletion

  e.next();

  $app.runInTransaction((txApp) => {
    // do something in the transaction
  });

  // after deletion
}, "users");
