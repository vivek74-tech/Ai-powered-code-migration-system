
import { Router } from "express";
import { validateCode } from "../controllers/validationController.js";

const router = Router();

router.post("/check", validateCode);

export default router;
