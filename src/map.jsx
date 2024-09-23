import React from "react";
import ReactDOM from "react-dom/client";
import App from "./MapApp.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("map")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
