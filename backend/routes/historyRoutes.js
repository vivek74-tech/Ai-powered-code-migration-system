
import { Router } from "express";

import {
  getHistory,
  getMigrationById,
  deleteMigration
} from "../controllers/historyController.js";

const router = Router();

router.get("/", getHistory);
router.get("/:id", getMigrationById);
router.delete("/:id", deleteMigration);

export default router;
