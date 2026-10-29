
import "dotenv/config";
import express from "express";
import cors from "cors";

import connectDB from "./config/db.js";
import migrationRoutes from "./routes/migrationRoutes.js";
import validationRoutes from "./routes/validationRoutes.js";
import historyRoutes from "./routes/historyRoutes.js";


const app = express();

app.use(cors({
  origin: "http://localhost:5173"
}));

app.use(express.json({ limit: "30kb" }));

app.get("/api/health", (req, res) => {
  res.json({
    success: true,
    message: "AI Code Migration API running"
  });
});

app.use("/api/migration", migrationRoutes);
app.use("/api/validation", validationRoutes);
app.use("/api/history", historyRoutes);
const PORT = process.env.PORT || 5000;

await connectDB();

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});
