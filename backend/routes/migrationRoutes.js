
import { Router } from "express";
import { migrateCode } from "../controllers/migrationController.js";

const router = Router();

router.post("/convert", migrateCode);

export default router;
