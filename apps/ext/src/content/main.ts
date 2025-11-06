import ContentApp from "./ContentApp.svelte";

const root = document.createElement("div");
const shadow = root.attachShadow({ mode: "open" });
document.documentElement.appendChild(root);

const mount = document.createElement("div");
shadow.appendChild(mount);

new ContentApp({ target: mount });
