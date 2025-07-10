# Deployment Guide for First-Aid Kit Tracker

This guide outlines the steps to modify your application code locally and deploy the changes to the live version hosted on Render.com.

## Workflow for Making and Deploying Changes

Follow these steps every time you want to update your application:

1.  **Make Local Code Changes:**
    *   Open your project files in the `E:/geminiCLI/first_aid_tracker` directory using your preferred code editor.
    *   Make all the necessary modifications to your Python (`.py`), JavaScript (`.js`), HTML (`.html`), CSS (`.css`), or any other relevant files.
    *   For example, you might have:
        *   Added sequence numbering to item lists in `static/app.js`.
        *   Implemented a download endpoint for `first_aid_kit.json` in `main.py`.
        *   Adjusted styling in `static/styles.css` for consistent table views.
    *   Save all your changes.

2.  **Navigate to Your Project Directory:**
    *   Open your command prompt (or terminal).
    *   Change your current directory to your project's root:
        ```bash
        cd E:/geminiCLI/first_aid_tracker
        ```

3.  **Stage Your Changes (Prepare for Commit):**
    *   Tell Git to include all your modified, new, or deleted files in the next commit. This adds them to the "staging area."
        ```bash
        git add .
        ```
    *   *(Optional: To see what changes are staged, you can run `git status`)*

4.  **Commit Your Changes (Save Locally):**
    *   Create a new "snapshot" (commit) of your project with the staged changes. You **must** provide a clear and descriptive message explaining what you changed.
        ```bash
        git commit -m "Your descriptive commit message here"
        ```
        *   **Example messages (ensure quotes are used for multi-word messages):**
            *   `git commit -m "Feat: Added expiry date validation"`
            *   `git commit -m "Fix: Corrected item removal bug"`
            *   `git commit -m "Refactor: Improved API endpoint for kit items"`
            *   `git commit -m "Docs: Updated deployment guide and added new feature examples"`

5.  **Push Your Changes to GitHub (Deploy):**
    *   Send your local commits from your computer to your remote GitHub repository (`https://github.com/psphang/first_aid_tracker.git`).
    *   This action will automatically trigger a new deployment on Render.com.
        ```bash
        git push origin master
        ```

## What Happens After Pushing?

*   Render.com detects the new changes in your GitHub repository.
*   It automatically pulls the latest code.
*   It runs the build command (`pip install -r requirements.txt`).
*   It restarts your application using the start command (`uvicorn main:app --host 0.0.0.0 --port $PORT`).
*   Your updated application will be live at `https://first-aid-tracker.onrender.com/` once the deployment is complete. You can monitor the deployment status on your Render.com dashboard.
