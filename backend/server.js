
import "dotenv/config";
import express from "express";
import cors from "cors";
import { rateLimit } from "express-rate-limit";

import connectDB from "./config/db.js";
import migrationRoutes from "./routes/migrationRoutes.js";
import validationRoutes from "./routes/validationRoutes.js";
import historyRoutes from "./routes/historyRoutes.js";

const app = express();

app.disable("x-powered-by");

const allowedOrigins = (
  process.env.FRONTEND_URL || "http://localhost:5173"
).split(",").map(origin => origin.trim());

app.use(cors({
  origin(origin, callback) {
    if (!origin || allowedOrigins.includes(origin)) {
      return callback(null, true);
    }
    return callback(new Error("CORS origin not allowed"));
  }
}));

app.use(express.json({ limit: "30kb" }));

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  limit: 100,
  standardHeaders: "draft-8",
  legacyHeaders: false,
  message: {
    success: false,
    message: "Too many requests. Try again later."
  }
});

const executionLimiter = rateLimit({
  windowMs: 60 * 1000,
  limit: 5,
  standardHeaders: "draft-8",
  legacyHeaders: false,
  message: {
    success: false,
    message: "Execution request limit reached."
  }
});

app.use("/api", apiLimiter);

app.get("/api/health", (req, res) => {
  res.json({
    success: true,
    message: "AI Code Migration API running"
  });
});

app.use("/api/migration", executionLimiter, migrationRoutes);
app.use("/api/validation", executionLimiter, validationRoutes);
app.use("/api/history", (req, res) => {
  return res.status(403).json({
    success: false,
    message: "History is temporarily disabled for security"
  });
});

app.use((err, req, res, next) => {
  if (err.type === "entity.too.large") {
    return res.status(413).json({
      success: false,
      message: "Request payload too large"
    });
  }

  if (err.message === "CORS origin not allowed") {
    return res.status(403).json({
      success: false,
      message: "Origin not allowed"
    });
  }

  console.error("API error:", err.message);

  res.status(500).json({
    success: false,
    message: "Internal server error"
  });
});

const PORT = process.env.PORT || 5000;

await connectDB();

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
