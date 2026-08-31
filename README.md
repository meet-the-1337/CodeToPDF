# Code to PDF 🚀

A high-performance, local-first desktop application that converts source code and plain text into clean, readable, and beautifully formatted PDFs.

This project is built not just as a tool, but as a **thinking system** — focused on solving problems with clarity, speed, and simplicity.

---

## ⚡ Quick Start

1. Download from GitHub Releases

2. Run:

Linux (AppImage)
chmod +x code-to-pdf.AppImage && ./code-to-pdf.AppImage

Linux (.deb)
sudo apt install ./code-to-pdf_1.0.0_amd64.deb

Windows
Run code-to-pdf-windows.exe

macOS
Open code-to-pdf-macos.dmg → drag app → run

Android (Phone)
Install code-to-pdf-android.apk → Open & Generate PDF

3. Open app → Select file or paste code → Generate PDF

---

## 🧠 Core Vision

This app is built on a simple principle:

Problem → Structure → Flow → Execution → Output

You are not building features.  
You are building **clear thinking systems**.

---

## 🧠 Problem Being Solved

Raw code is:
- Hard to read
- Poorly formatted
- Not presentation-ready

Goal:
Convert it into a **clean, structured, readable PDF** with minimal effort.

---

## 🔁 High-Level Flow

User Input
↓
Detect Input Type
↓
Detect Language
↓
Apply Formatting
↓
Optimize Processing
↓
Generate PDF
↓
Save Output

---

## 🔄 Detailed Flowchart

[User Input]
↓
[File Selected OR Code Pasted]
↓
[Detect Language using Pygments]
↓
Is Code?
→ Yes → Syntax Highlighting
→ No → Plain Text Styling
↓
[Apply Font + Theme + Background]
↓
[Chunk Processing (for large inputs)]
↓
[Convert to PDF (ReportLab)]
↓
[Store in Memory (BytesIO)]
↓
[Write Final Output File]

---

## ⚙️ System Architecture

GUI Layer (PyQt6)
↓
Input Controller
↓
Processing Engine
↓
Pygments (Tokenization + Highlighting)
↓
ReportLab (PDF Rendering)
↓
BytesIO (Memory Buffer)
↓
Output File

---

## 🔧 Internal Processing Steps

1. Accept input (file or pasted text)  
2. Identify language automatically  
3. Tokenize content using Pygments  
4. Map tokens to styles (colors/fonts)  
5. Group lines into chunks (memory efficient)  
6. Build PDF elements using ReportLab  
7. Render into memory (no disk temp files)  
8. Save final PDF  

---

## ⚡ Performance Design

Key idea: **Do less, but do it efficiently**

Strategies:

- In-memory processing (BytesIO)
- Font caching (avoid reloading fonts)
- Style caching (avoid recomputation)
- Chunk-based rendering (avoid memory spikes)
- Background threads (no UI freeze)

---

## 📊 Performance Metrics

Startup Time: ~130 ms  
1000 Lines PDF: ~0.4 seconds  
Cached Re-run: ~6 ms  
Idle RAM: ~37 MB  
Peak RAM: < 130 MB  
Temp Disk Usage: 0  

---

## 🧪 Example Flow

Input: main.cpp

Step 1: Detect C++  
Step 2: Apply syntax highlighting  
Step 3: Format into structured layout  
Step 4: Render into PDF  
Step 5: Save as main_code.pdf  

---

## 🌐 Cross-Platform Strategy

Single Codebase
↓
Multiple Build Targets

Linux:
- AppImage (portable)
- .deb (Debian/Ubuntu)
- .rpm (Fedora/openSUSE)

Windows:
- .exe (PyInstaller)

macOS:
- .dmg (native app bundle)

Android (Phone):
- .apk (Buildozer / Kivy touch mobile app)

---

## 📦 Build & Distribution Flow

Source Code
↓
PyInstaller Build
↓
Platform Packaging
↓
GitHub Actions CI/CD
↓
Release Assets
↓
User Download

---

## 🔁 User Journey

Download App
↓
Run / Install
↓
Open Interface
↓
Paste or Select Code
↓
Click Generate
↓
Get PDF

---

## 🧠 Design Philosophy

Simple Input  
↓  
Clear Flow  
↓  
Fast Output  

Avoid:
- Over-engineering  
- Heavy UI  
- Unnecessary features  

---

## 🧠 Your Thinking Model

See Problem  
↓  
Break into Steps  
↓  
Design Flow  
↓  
Build Minimal Solution  
↓  
Optimize Later  

This app is training that mindset.

---

## 🔭 Future Direction

Real-world problems
↓
Flow-based solutions
↓
Minimal tools
↓
Fast execution
↓
Scalable thinking

---

## 📁 Project Structure

CodeToPDF/
├── src/
│   ├── gui.py
│   ├── code_to_pdf_engine.py
├── assets/
├── .github/workflows/
├── build scripts
├── README.md

---

## 🧠 Mental Model

Don't think:
"Build complex apps"

Think:
"Solve one problem clearly"

---

## 🔚 Final Thought

If it is:
- Fast
- Simple
- Predictable

Then it is correct.
