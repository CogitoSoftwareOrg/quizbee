import { mount } from "svelte";

import "../app.css";
import Popup from "./Popup.svelte";

const app = mount(Popup, {
  target: document.getElementById("app")!,
});

export default app;
