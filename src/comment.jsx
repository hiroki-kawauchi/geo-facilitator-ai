import React from "react";
import ReactDOM from "react-dom/client";
import App from "./CommentApp.jsx";
import "./index.css";

ReactDOM.createRoot(document.getElementById("comment")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
