
import mongoose from "mongoose";
import Migration from "../models/Migration.js";

// Get latest conversion history
export const getHistory = async (req, res) => {
  try {
    const history = await Migration.find()
      .sort({ createdAt: -1 })
      .limit(50)
      .lean();

    return res.status(200).json({
      success: true,
      count: history.length,
      history
    });
  } catch (error) {
    return res.status(500).json({
      success: false,
      message: "Failed to fetch history"
    });
  }
};

// Get one conversion
export const getMigrationById = async (req, res) => {
  try {
    const { id } = req.params;

    if (!mongoose.isValidObjectId(id)) {
      return res.status(400).json({
        success: false,
        message: "Invalid migration ID"
      });
    }

    const migration = await Migration.findById(id);

    if (!migration) {
      return res.status(404).json({
        success: false,
        message: "Migration not found"
      });
    }

    return res.json({
      success: true,
      migration
    });
  } catch (error) {
    return res.status(500).json({
      success: false,
      message: "Failed to fetch migration"
    });
  }
};

// Delete conversion
export const deleteMigration = async (req, res) => {
  try {
    const { id } = req.params;

    if (!mongoose.isValidObjectId(id)) {
      return res.status(400).json({
        success: false,
        message: "Invalid migration ID"
      });
    }

    const migration = await Migration.findByIdAndDelete(id);

    if (!migration) {
      return res.status(404).json({
        success: false,
        message: "Migration not found"
      });
    }

    return res.json({
      success: true,
      message: "Migration deleted successfully"
    });
  } catch (error) {
    return res.status(500).json({
      success: false,
      message: "Failed to delete migration"
    });
  }
};
