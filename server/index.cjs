/**
 * Weather App — Node.js upload/proxy server
 * Handles community photo uploads and serves static files.
 * Run with: node server/index.cjs
 */

const express = require("express");
const cors = require("cors");
const multer = require("multer");
const path = require("path");
const fs = require("fs");

const app = express();
const PORT = process.env.UPLOAD_PORT || 3001;
const UPLOAD_DIR = path.join(__dirname, "uploads");

// Ensure upload directory exists
if (!fs.existsSync(UPLOAD_DIR)) fs.mkdirSync(UPLOAD_DIR, { recursive: true });

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------

app.use(cors({ origin: ["http://localhost:3000", "http://127.0.0.1:3000"] }));
app.use(express.json());

// Serve uploaded files statically
app.use("/uploads", express.static(UPLOAD_DIR));

// ---------------------------------------------------------------------------
// Multer — photo uploads (images only, max 10 MB)
// ---------------------------------------------------------------------------

const storage = multer.diskStorage({
  destination: (_req, _file, cb) => cb(null, UPLOAD_DIR),
  filename: (_req, file, cb) => {
    const ext = path.extname(file.originalname).toLowerCase() || ".jpg";
    const name = `${Date.now()}-${Math.random().toString(36).slice(2)}${ext}`;
    cb(null, name);
  },
});

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10 MB
  fileFilter: (_req, file, cb) => {
    if (file.mimetype.startsWith("image/")) {
      cb(null, true);
    } else {
      cb(new Error("Only image files are allowed"), false);
    }
  },
});

// ---------------------------------------------------------------------------
// Routes
// ---------------------------------------------------------------------------

/** Upload a community weather photo */
app.post("/upload/photo", upload.single("file"), (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file uploaded or invalid type" });
  }
  res.json({
    url: `/uploads/${req.file.filename}`,
    filename: req.file.filename,
    size: req.file.size,
  });
});

/** Delete an uploaded photo by filename */
app.delete("/upload/photo/:filename", (req, res) => {
  const { filename } = req.params;
  // Prevent path traversal
  if (filename.includes("..") || filename.includes("/")) {
    return res.status(400).json({ error: "Invalid filename" });
  }
  const filePath = path.join(UPLOAD_DIR, filename);
  if (!fs.existsSync(filePath)) {
    return res.status(404).json({ error: "File not found" });
  }
  fs.unlinkSync(filePath);
  res.json({ deleted: filename });
});

/** List all uploaded photos */
app.get("/upload/photos", (_req, res) => {
  const files = fs.readdirSync(UPLOAD_DIR).map((name) => ({
    filename: name,
    url: `/uploads/${name}`,
    size: fs.statSync(path.join(UPLOAD_DIR, name)).size,
  }));
  res.json({ photos: files });
});

/** Health check */
app.get("/health", (_req, res) => res.json({ status: "ok", port: PORT }));

// ---------------------------------------------------------------------------
// Error handler
// ---------------------------------------------------------------------------

app.use((err, _req, res, _next) => {
  console.error(err.message);
  res.status(err.status || 500).json({ error: err.message });
});

// ---------------------------------------------------------------------------
// Start
// ---------------------------------------------------------------------------

app.listen(PORT, () => {
  console.log(`Upload server running at http://localhost:${PORT}`);
});
