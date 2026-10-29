import { Router } from "express";
import { timingSafeEqual } from "node:crypto";
import { migrateCode } from "../controllers/migrationController.js";

const router = Router();

router.post("/convert", (req, res, next) => {
  const expected = process.env.DEMO_ACCESS_KEY;
  const supplied = req.get("X-Demo-Key") || "";

  if (!expected) {
    return res.status(503).json({ message: "Demo access not configured" });
  }

  const a = Buffer.from(supplied);
  const b = Buffer.from(expected);

  if (a.length !== b.length || !timingSafeEqual(a, b)) {
    return res.status(403).json({ message: "Forbidden" });
  }

  next();
}, migrateCode);

export default router;
