import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import { installDevBridgeIfRequested } from "./services/devBridge.js";
import "./styles.css";

installDevBridgeIfRequested(); // no-op inside the desktop app (PyWebView provides window.pywebview.api)

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
