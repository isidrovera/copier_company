/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// ─── Bootstrap Icons SVG paths por extensión ─────────────────────────────────
// Usamos iconos SVG inline para máxima fidelidad visual

const FILE_TYPES = {
    // PDF
    pdf:  {
        color: "#dc2626", bg: "#fef2f2",
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="9" y1="13" x2="15" y2="13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <line x1="9" y1="17" x2="15" y2="17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
            <text x="7" y="13" font-size="5" font-weight="700" fill="currentColor" font-family="sans-serif">PDF</text>
        </svg>`,
        label: "PDF",
        previewable: true,
    },
    // Word
    doc:  { color: "#1d4ed8", bg: "#eff6ff", label: "DOC",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><line x1="9" y1="13" x2="15" y2="13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="9" y1="17" x2="15" y2="17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>` },
    docx: { color: "#1d4ed8", bg: "#eff6ff", label: "DOCX", previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><line x1="9" y1="13" x2="15" y2="13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="9" y1="17" x2="15" y2="17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>` },
    // Excel
    xls:  { color: "#16a34a", bg: "#f0fdf4", label: "XLS",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="8" y="12" width="8" height="6" rx="0.5" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="12" x2="12" y2="18" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="15" x2="16" y2="15" stroke="currentColor" stroke-width="1.5"/></svg>` },
    xlsx: { color: "#16a34a", bg: "#f0fdf4", label: "XLSX", previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="8" y="12" width="8" height="6" rx="0.5" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="12" x2="12" y2="18" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="15" x2="16" y2="15" stroke="currentColor" stroke-width="1.5"/></svg>` },
    xlsm: { color: "#16a34a", bg: "#f0fdf4", label: "XLSM", previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="8" y="12" width="8" height="6" rx="0.5" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="12" x2="12" y2="18" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="15" x2="16" y2="15" stroke="currentColor" stroke-width="1.5"/></svg>` },
    csv:  { color: "#15803d", bg: "#f0fdf4", label: "CSV",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="8" y="12" width="8" height="6" rx="0.5" stroke="currentColor" stroke-width="1.5"/><line x1="12" y1="12" x2="12" y2="18" stroke="currentColor" stroke-width="1.5"/><line x1="8" y1="15" x2="16" y2="15" stroke="currentColor" stroke-width="1.5"/></svg>` },
    // PowerPoint
    ppt:  { color: "#ea580c", bg: "#fff7ed", label: "PPT",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="8.5" y="11.5" width="7" height="5" rx="1.5" stroke="currentColor" stroke-width="1.5"/></svg>` },
    pptx: { color: "#ea580c", bg: "#fff7ed", label: "PPTX", previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="8.5" y="11.5" width="7" height="5" rx="1.5" stroke="currentColor" stroke-width="1.5"/></svg>` },
    txt:  { color: "#475569", bg: "#f8fafc", label: "TXT",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><line x1="9" y1="13" x2="15" y2="13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><line x1="9" y1="17" x2="13" y2="17" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>` },
    // Imágenes — previewable
    jpg:  { color: "#7c3aed", bg: "#f5f3ff", label: "JPG",  previewable: true,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.8"/><circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" stroke-width="1.5"/><polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    jpeg: { color: "#7c3aed", bg: "#f5f3ff", label: "JPEG", previewable: true,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.8"/><circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" stroke-width="1.5"/><polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    png:  { color: "#7c3aed", bg: "#f5f3ff", label: "PNG",  previewable: true,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.8"/><circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" stroke-width="1.5"/><polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    gif:  { color: "#7c3aed", bg: "#f5f3ff", label: "GIF",  previewable: true,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.8"/><circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" stroke-width="1.5"/><polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    webp: { color: "#7c3aed", bg: "#f5f3ff", label: "WEBP", previewable: true,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.8"/><circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" stroke-width="1.5"/><polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    svg:  { color: "#7c3aed", bg: "#f5f3ff", label: "SVG",  previewable: true,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.8"/><circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" stroke-width="1.5"/><polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    bmp:  { color: "#7c3aed", bg: "#f5f3ff", label: "BMP",  previewable: true,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" stroke-width="1.8"/><circle cx="8.5" cy="8.5" r="1.5" stroke="currentColor" stroke-width="1.5"/><polyline points="21 15 16 10 5 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    // Comprimidos
    zip:  { color: "#b45309", bg: "#fffbeb", label: "ZIP",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="17 21 17 13 13 13 13 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="13 17 17 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><line x1="11" y1="3" x2="11" y2="11" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-dasharray="2 2"/></svg>` },
    rar:  { color: "#b45309", bg: "#fffbeb", label: "RAR",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="17 21 17 13 13 13 13 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="13 17 17 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>` },
    "7z": { color: "#b45309", bg: "#fffbeb", label: "7Z",   previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="17 21 17 13 13 13 13 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="13 17 17 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>` },
    tar:  { color: "#b45309", bg: "#fffbeb", label: "TAR",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="17 21 17 13 13 13 13 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="13 17 17 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>` },
    gz:   { color: "#b45309", bg: "#fffbeb", label: "GZ",   previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="17 21 17 13 13 13 13 21" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="13 17 17 17" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>` },
    // Video
    mp4:  { color: "#be123c", bg: "#fff1f2", label: "MP4",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polygon points="23 7 16 12 23 17 23 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="1" y="5" width="15" height="14" rx="2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    avi:  { color: "#be123c", bg: "#fff1f2", label: "AVI",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polygon points="23 7 16 12 23 17 23 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="1" y="5" width="15" height="14" rx="2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    mov:  { color: "#be123c", bg: "#fff1f2", label: "MOV",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polygon points="23 7 16 12 23 17 23 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="1" y="5" width="15" height="14" rx="2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    mkv:  { color: "#be123c", bg: "#fff1f2", label: "MKV",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polygon points="23 7 16 12 23 17 23 7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><rect x="1" y="5" width="15" height="14" rx="2" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    // Audio
    mp3:  { color: "#6d28d9", bg: "#f5f3ff", label: "MP3",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 18V5l12-2v13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="1.8"/><circle cx="18" cy="16" r="3" stroke="currentColor" stroke-width="1.8"/></svg>` },
    wav:  { color: "#6d28d9", bg: "#f5f3ff", label: "WAV",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 18V5l12-2v13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="1.8"/><circle cx="18" cy="16" r="3" stroke="currentColor" stroke-width="1.8"/></svg>` },
    flac: { color: "#6d28d9", bg: "#f5f3ff", label: "FLAC", previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 18V5l12-2v13" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><circle cx="6" cy="18" r="3" stroke="currentColor" stroke-width="1.8"/><circle cx="18" cy="16" r="3" stroke="currentColor" stroke-width="1.8"/></svg>` },
    // Código
    js:   { color: "#ca8a04", bg: "#fefce8", label: "JS",   previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    py:   { color: "#2563eb", bg: "#eff6ff", label: "PY",   previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    php:  { color: "#7e22ce", bg: "#faf5ff", label: "PHP",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    html: { color: "#c2410c", bg: "#fff7ed", label: "HTML", previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    css:  { color: "#0369a1", bg: "#f0f9ff", label: "CSS",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    json: { color: "#374151", bg: "#f9fafb", label: "JSON", previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    xml:  { color: "#166534", bg: "#f0fdf4", label: "XML",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="16 18 22 12 16 6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="8 6 2 12 8 18" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    // Firmware / binarios
    bin:  { color: "#1f2937", bg: "#f3f4f6", label: "BIN",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="2" width="20" height="20" rx="3" stroke="currentColor" stroke-width="1.8"/><path d="M8 8v8M12 8l4 4-4 4M6 12h2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    hex:  { color: "#1f2937", bg: "#f3f4f6", label: "HEX",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="2" width="20" height="20" rx="3" stroke="currentColor" stroke-width="1.8"/><path d="M8 8v8M12 8l4 4-4 4M6 12h2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    fw:   { color: "#1f2937", bg: "#f3f4f6", label: "FW",   previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="2" y="2" width="20" height="20" rx="3" stroke="currentColor" stroke-width="1.8"/><path d="M8 8v8M12 8l4 4-4 4M6 12h2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>` },
    iso:  { color: "#1f2937", bg: "#f3f4f6", label: "ISO",  previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.8"/></svg>` },
};

// Colores de carpeta por hash de nombre
const FOLDER_COLORS = ["#f59e0b","#f97316","#ef4444","#ec4899","#8b5cf6","#3b82f6","#06b6d4","#10b981"];
function getFolderColor(name) {
    let h = 0; for (let i = 0; i < name.length; i++) h += name.charCodeAt(i);
    return FOLDER_COLORS[h % FOLDER_COLORS.length];
}

// SVG de carpeta
const FOLDER_SVG = `<svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
    <path d="M10 4H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-8l-2-2z"/>
</svg>`;

function getFileType(name, isFolder) {
    if (isFolder) return {
        color: getFolderColor(name), bg: "#fffbeb",
        svg: FOLDER_SVG, label: "DIR", previewable: false,
    };
    const ext = name.split(".").pop().toLowerCase();
    return FILE_TYPES[ext] || {
        color: "#64748b", bg: "#f8fafc", label: ext.toUpperCase().slice(0,4) || "FILE", previewable: false,
        svg: `<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    };
}

function formatSize(bytes) {
    if (!bytes) return "";
    const u = ["B","KB","MB","GB","TB"]; let s = bytes, i = 0;
    while (s >= 1024 && i < u.length - 1) { s /= 1024; i++; }
    return `${s.toFixed(1)} ${u[i]}`;
}

function formatDate(str) {
    if (!str) return "";
    try { return new Date(str).toLocaleDateString("es-PE", { day:"2-digit", month:"short", year:"numeric" }); }
    catch { return str; }
}

// ─── Componente Principal ─────────────────────────────────────────────────────

class PCloudExplorer extends Component {
    static template = "copier_company.PCloudExplorer";

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.state = useState({
            items: [],
            breadcrumbs: [{ id: "0", name: "Mi pCloud" }],
            currentFolderId: "0",
            loading: false,
            error: null,

            selectedIds: new Set(),
            viewMode: "grid",
            searchQuery: "",

            // Modales
            modal: null,
            modalData: {},

            // Drag & drop
            dragItemId: null,
            dragOverId: null,

            // Context menu
            contextMenu: null,

            // Panel crear productos
            showCreatePanel: false,
            createPricePen: 100,
            createPriceUsd: 25,
            createResults: [],
            creatingProducts: false,

            // Previsualización de archivos
            previewItem: null,
            previewUrl: null,
            previewLoading: false,
        });

        onWillStart(() => this._loadContents("0"));
    }

    // ─── Navegación ───────────────────────────────────────────────────────────

    async _loadContents(folderId) {
        this.state.loading = true;
        this.state.error = null;
        this.state.selectedIds = new Set();
        this.state.showCreatePanel = false;
        this.state.createResults = [];
        try {
            const items = await this.orm.call("pcloud.config", "pcloud_list_contents", [parseInt(folderId)]);
            this.state.items = items;
            this.state.currentFolderId = String(folderId);
        } catch (e) {
            const msg = e.data?.message || e.message || "Error al conectar con pCloud";
            this.state.error = msg;
            this.notification.add(msg, { type: "danger" });
        } finally {
            this.state.loading = false;
        }
    }

    // ─── Click en ítem: un click abre carpeta o previsualiza archivo ──────────
    async onItemClick(item, ev) {
        // Si el click viene del checkbox (o sus hijos), ignorar aquí
        if (ev.target.closest(".pce_item_checkbox")) return;

        if (item.is_folder) {
            // Navegar a la carpeta
            this.state.breadcrumbs.push({ id: item.id, name: item.name });
            await this._loadContents(item.id);
        } else {
            // Abrir/previsualizar archivo
            await this.openFilePreview(item);
        }
    }

    // ─── Click en checkbox: toggle selección ─────────────────────────────────
    onCheckboxClick(item, ev) {
        ev.stopPropagation();
        if (ev.shiftKey) {
            const all = this.filteredItems;
            const lastIdx = all.findIndex(i => i.id === [...this.state.selectedIds].pop());
            const currIdx = all.findIndex(i => i.id === item.id);
            if (lastIdx >= 0) {
                const [from, to] = [Math.min(lastIdx, currIdx), Math.max(lastIdx, currIdx)];
                const ids = new Set(this.state.selectedIds);
                all.slice(from, to + 1).forEach(i => ids.add(i.id));
                this.state.selectedIds = ids;
            } else {
                this.state.selectedIds = new Set([item.id]);
            }
        } else {
            const ids = new Set(this.state.selectedIds);
            ids.has(item.id) ? ids.delete(item.id) : ids.add(item.id);
            this.state.selectedIds = ids;
        }
        this.state.showCreatePanel = this.selectedFolderItems.length > 0;
    }

    async onBreadcrumbClick(crumb, index) {
        this.state.breadcrumbs = this.state.breadcrumbs.slice(0, index + 1);
        await this._loadContents(crumb.id);
    }

    // ─── Previsualización de archivos ─────────────────────────────────────────

    async openFilePreview(item) {
        if (item.is_folder) return;
        const ft = getFileType(item.name, false);

        this.state.previewItem = item;
        this.state.previewUrl = null;
        this.state.previewLoading = true;
        this.state.modal = "preview";

        try {
            const url = await this.orm.call("pcloud.config", "pcloud_get_file_download_url", [item.id]);
            this.state.previewUrl = url;
        } catch (e) {
            this.notification.add(e.data?.message || "Error al obtener archivo", { type: "danger" });
            this.closeModal();
        } finally {
            this.state.previewLoading = false;
        }
    }

    getPreviewType(item) {
        if (!item) return "unknown";
        const ext = item.name.split(".").pop().toLowerCase();
        if (["jpg","jpeg","png","gif","webp","svg","bmp"].includes(ext)) return "image";
        if (ext === "pdf") return "pdf";
        if (["mp4","webm","ogg"].includes(ext)) return "video";
        if (["mp3","wav","ogg","flac"].includes(ext)) return "audio";
        return "download";
    }

    // ─── Selección ────────────────────────────────────────────────────────────

    toggleSelectAll() {
        if (this.state.selectedIds.size === this.filteredItems.length) {
            this.state.selectedIds = new Set();
            this.state.showCreatePanel = false;
        } else {
            this.state.selectedIds = new Set(this.filteredItems.map(i => i.id));
            this.state.showCreatePanel = this.selectedFolderItems.length > 0;
        }
    }

    isSelected(item) { return this.state.selectedIds.has(item.id); }

    get selectedItems() { return this.state.items.filter(i => this.state.selectedIds.has(i.id)); }
    get selectedFolderItems() { return this.selectedItems.filter(i => i.is_folder); }

    // ─── Modales ──────────────────────────────────────────────────────────────

    openModal(type, data = {}) { this.state.modal = type; this.state.modalData = { ...data }; }

    closeModal() {
        this.state.modal = null;
        this.state.modalData = {};
        this.state.previewItem = null;
        this.state.previewUrl = null;
    }

    // ─── Crear carpeta ────────────────────────────────────────────────────────

    openNewFolderModal() { this.openModal("newFolder", { name: "" }); }

    async confirmNewFolder() {
        const name = this.state.modalData.name?.trim();
        if (!name) return;
        try {
            await this.orm.call("pcloud.config", "pcloud_create_folder", [name, parseInt(this.state.currentFolderId)]);
            this.notification.add(`Carpeta "${name}" creada`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al crear carpeta", { type: "danger" });
        }
    }

    // ─── Renombrar ────────────────────────────────────────────────────────────

    openRenameModal(item) { this.openModal("rename", { item, newName: item.name }); }

    async confirmRename() {
        const { item, newName } = this.state.modalData;
        if (!newName?.trim() || newName === item.name) { this.closeModal(); return; }
        try {
            await this.orm.call("pcloud.config", "pcloud_rename", [item.id, newName.trim(), item.is_folder]);
            this.notification.add(`Renombrado a "${newName}"`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al renombrar", { type: "danger" });
        }
    }

    // ─── Eliminar ─────────────────────────────────────────────────────────────

    async deleteSelected() {
        const items = this.selectedItems;
        if (!items.length) return;
        const label = items.length > 1 ? `${items.length} elementos` : `"${items[0].name}"`;
        if (!confirm(`¿Eliminar ${label}? Esta acción no se puede deshacer.`)) return;
        try {
            for (const item of items) {
                await this.orm.call("pcloud.config", "pcloud_delete", [item.id, item.is_folder]);
            }
            this.notification.add("Eliminado correctamente", { type: "success" });
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al eliminar", { type: "danger" });
        }
    }

    async onDeleteRowClick(item, ev) {
        ev.stopPropagation();
        const ids = new Set([item.id]);
        this.state.selectedIds = ids;
        await this.deleteSelected();
    }

    // ─── Subir archivo ────────────────────────────────────────────────────────

    openUploadModal() { this.openModal("upload", { files: [] }); }

    onFileInputChange(ev) { this.state.modalData.files = Array.from(ev.target.files); }

    async confirmUpload() {
        const files = this.state.modalData.files;
        if (!files?.length) return;
        this.state.modalData.uploading = true;
        let uploaded = 0;
        try {
            for (const file of files) {
                const b64 = await this._fileToBase64(file);
                await this.orm.call("pcloud.config", "pcloud_upload", [file.name, b64, parseInt(this.state.currentFolderId)]);
                uploaded++;
            }
            this.notification.add(`${uploaded} archivo(s) subido(s)`, { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al subir", { type: "danger" });
        } finally {
            this.state.modalData.uploading = false;
        }
    }

    _fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const r = new FileReader();
            r.onload = () => resolve(r.result.split(",")[1]);
            r.onerror = reject;
            r.readAsDataURL(file);
        });
    }

    // ─── Compartir ────────────────────────────────────────────────────────────

    async openShareModal(item) {
        if (!item.is_folder) return;
        this.openModal("share", { item, loading: true, link: null });
        try {
            const result = await this.orm.call("pcloud.config", "pcloud_get_share_link", [item.id]);
            this.state.modalData.link = result.link;
            this.state.modalData.code = result.code;
        } catch (e) {
            this.state.modalData.error = e.data?.message || "Error al obtener link";
        } finally {
            this.state.modalData.loading = false;
        }
    }

    copyShareLink() {
        const link = this.state.modalData.link;
        if (!link) return;
        navigator.clipboard.writeText(link).then(() => {
            this.notification.add("Link copiado", { type: "success" });
        });
    }

    async deleteShareLink() {
        try {
            await this.orm.call("pcloud.config", "pcloud_delete_share_link", [this.state.modalData.code]);
            this.notification.add("Link revocado", { type: "success" });
            this.closeModal();
        } catch (e) {
            this.notification.add(e.data?.message || "Error al revocar", { type: "danger" });
        }
    }

    // ─── Mover ────────────────────────────────────────────────────────────────

    openMoveModal() {
        if (!this.selectedItems.length) return;
        this.openModal("move", { items: this.selectedItems, targetFolderId: "" });
    }

    async confirmMove() {
        const { items, targetFolderId } = this.state.modalData;
        if (!targetFolderId) return;
        try {
            for (const item of items) {
                await this.orm.call("pcloud.config", "pcloud_move", [item.id, targetFolderId, item.is_folder]);
            }
            this.notification.add("Movido correctamente", { type: "success" });
            this.closeModal();
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al mover", { type: "danger" });
        }
    }

    // ─── Descargar ────────────────────────────────────────────────────────────

    async downloadFile(item) {
        if (item.is_folder) return;
        try {
            const url = await this.orm.call("pcloud.config", "pcloud_get_file_download_url", [item.id]);
            // Crear link temporal para forzar descarga
            const a = document.createElement("a");
            a.href = url;
            a.download = item.name;
            a.target = "_blank";
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al descargar", { type: "danger" });
        }
    }

    // ─── Crear productos desde carpetas ───────────────────────────────────────

    toggleCreatePanel() {
        this.state.showCreatePanel = !this.state.showCreatePanel;
        this.state.createResults = [];
    }

    async confirmCreateProducts() {
        const folders = this.selectedFolderItems.map(i => ({ id: i.id, name: i.name }));
        if (!folders.length) { this.notification.add("Selecciona al menos una carpeta", { type: "warning" }); return; }
        const pricePen = parseFloat(this.state.createPricePen) || 100;
        const priceUsd = parseFloat(this.state.createPriceUsd) || 25;
        this.state.creatingProducts = true;
        this.state.createResults = [];
        try {
            const results = await this.orm.call("pcloud.config", "pcloud_create_products_from_folders", [folders, pricePen, priceUsd]);
            this.state.createResults = results;
            const created  = results.filter(r => r.status === "created").length;
            const existing = results.filter(r => r.status === "already_exists").length;
            const errors   = results.filter(r => r.status === "error").length;
            if (created > 0) this.notification.add(`${created} producto(s) creado(s)${existing ? `, ${existing} ya existía(n)` : ""}`, { type: "success" });
            else if (existing > 0 && errors === 0) this.notification.add("Todos los productos ya existen", { type: "info" });
            if (errors > 0) this.notification.add(`${errors} error(es) al crear productos`, { type: "danger" });
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al crear productos", { type: "danger" });
        } finally {
            this.state.creatingProducts = false;
        }
    }

    getCreateResultIcon(status) {
        return { created: "✅", already_exists: "⚠️", error: "❌" }[status] || "❓";
    }

    // ─── Drag & drop ──────────────────────────────────────────────────────────

    onDragStart(item, ev) { this.state.dragItemId = item.id; ev.dataTransfer.effectAllowed = "move"; }

    onDragOver(item, ev) {
        if (!item.is_folder || item.id === this.state.dragItemId) return;
        ev.preventDefault(); this.state.dragOverId = item.id;
    }

    onDragLeave() { this.state.dragOverId = null; }

    async onDrop(targetItem, ev) {
        ev.preventDefault();
        const dragId = this.state.dragItemId;
        this.state.dragItemId = null; this.state.dragOverId = null;
        if (!dragId || !targetItem.is_folder || dragId === targetItem.id) return;
        const dragged = this.state.items.find(i => i.id === dragId);
        if (!dragged) return;
        try {
            await this.orm.call("pcloud.config", "pcloud_move", [dragId, targetItem.id, dragged.is_folder]);
            this.notification.add(`"${dragged.name}" movido a "${targetItem.name}"`, { type: "success" });
            await this._loadContents(this.state.currentFolderId);
        } catch (e) {
            this.notification.add(e.data?.message || "Error al mover", { type: "danger" });
        }
    }

    // ─── Context menu ─────────────────────────────────────────────────────────

    onContextMenu(item, ev) {
        ev.preventDefault();
        this.state.selectedIds = new Set([item.id]);
        this.state.contextMenu = { x: ev.clientX, y: ev.clientY, item };
    }

    closeContextMenu() { this.state.contextMenu = null; }

    // ─── Búsqueda ─────────────────────────────────────────────────────────────

    get filteredItems() {
        const q = this.state.searchQuery.toLowerCase().trim();
        if (!q) return this.state.items;
        return this.state.items.filter(i => i.name.toLowerCase().includes(q));
    }

    // ─── Helpers template ─────────────────────────────────────────────────────

    getFileType(item) { return getFileType(item.name, item.is_folder); }
    getFormattedSize(item) { return item.is_folder ? "" : formatSize(item.size); }
    getFormattedDate(item) { return formatDate(item.modified); }

    get allSelected() {
        return this.filteredItems.length > 0 && this.state.selectedIds.size === this.filteredItems.length;
    }
}

registry.category("actions").add("pcloud_explorer_action", PCloudExplorer);