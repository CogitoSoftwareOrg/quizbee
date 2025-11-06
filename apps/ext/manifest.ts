import { defineManifest } from "@crxjs/vite-plugin";

export default defineManifest({
  manifest_version: 3,
  name: "Quizbee Extension",
  description: "Quizbee Extension",
  version: "0.0.1",
  action: {
    default_title: "Quizbee Popup",
    default_popup: "index.html",
  },
  background: { service_worker: "src/background/index.ts", type: "module" },
  permissions: ["storage"],
  host_permissions: ["https://*/*", "http://*/*"],
  content_scripts: [
    {
      matches: ["<all_urls>"],
      js: ["src/content/main.ts"],
      run_at: "document_idle",
    },
  ],
});
