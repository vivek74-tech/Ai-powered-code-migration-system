
import { Router } from "express";
import { executeCode } from "../controllers/executionController.js";

const router = Router();

router.post("/run", executeCode);

export default router;
