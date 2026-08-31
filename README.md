# Code to PDF Converter 🚀

A fast, local-first desktop app that turns code or text into clean, readable PDFs.  
Built with performance, simplicity, and real-world usability in mind.

---

## 🧠 How This App Thinks (Core Idea)

User gives input → system understands type → applies minimal styling → outputs readable PDF fast.

Flow:

[User Input]  
↓  
[Detect: File OR Pasted Text]  
↓  
[Is Code?]  
↙        ↘  
[Yes]      [No]  
↓           ↓  
[Syntax]   [Plain Text Styling]  
[Highlight]  
↓  
[Font + Background Applied]  
↓  
[Chunk Processing (for large files)]  
↓  
[PDF Generated in Memory]  
↓  
[Saved Locally]

---

## ⚙️ System Design Flow

[GUI (PyQt6)]  
↓  
[Input Handler]  
↓  
[Engine (code_to_pdf_engine.py)]  
↓  
[Pygments → Language + Tokens]  
↓  
[ReportLab → PDF Builder]  
↓  
[BytesIO Buffer]  
↓  
[Final PDF Output]

---

## 🧩 Problem Solving Approach

This app is built on a simple belief:

Small problems → clear steps → efficient solution

Example problem:  
“Convert messy code into readable format”

Solution thinking:  
1. Identify input type  
2. Reduce complexity (no heavy styling)  
3. Keep processing local  
4. Optimize only where needed  
5. Deliver fast output  

---

## 🔁 Internal Processing Logic

Step 1: Input received  
Step 2: Mode selected (file / paste)  
Step 3: Language guessed  
Step 4: Tokens generated  
Step 5: Styles applied  
Step 6: Content chunked  
Step 7: PDF built in memory  
Step 8: Output saved  

---

## ⚡ Performance Philosophy

- Avoid unnecessary work  
- Cache everything reusable  
- Never block UI  
- Never use disk if memory works  

Result:
- < 0.5s generation  
- < 150MB peak RAM  
- 0 temp files  

---

## 🧪 Example Flow (Real Use)

Input: `main.cpp`  

→ detected as C++  
→ keywords colored  
→ formatted into blocks  
→ rendered into PDF  
→ saved as `main_code_to_pdf.pdf`  

---

## 🎯 Design Principles

- Local-first (no internet ever)  
- Fast over fancy  
- Simple UI > complex features  
- Predictable output  
- Minimal clicks  

---

## 🚀 Your Bigger Vision

You’re not just building this app.

You’re learning:

- How to break problems  
- How to design flow  
- How to optimize thinking  
- How to build tools people actually use  

Future direction:

[Problem]  
↓  
[Break into steps]  
↓  
[Design flow]  
↓  
[Build simple tool]  
↓  
[Optimize only when needed]  

Repeat.

---

## 📁 Project Structure

CodeToPDF/  
├── src/  
│   ├── gui.py  
│   ├── code_to_pdf_engine.py  
├── dist/  
│   └── code-to-pdf  
├── assets/  
│   └── icon.png  
├── setup_shortcut.sh  
├── code-to-pdf.desktop  
├── README.md  

---

## 🧠 Mental Model

Don’t think:  
“Build big apps”

Think:  
“Solve one clear problem cleanly”

---

## ⚡ Run App
