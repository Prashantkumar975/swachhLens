# SwachhLens — Deployment & Update Guide

## 🚀 Quick Start

### Local Development
```bash
# Start dev server (static frontend)
node dev-server.js
# → http://127.0.0.1:3000

# Start backend (if needed)
powershell .\launch-backend.ps1
```

### Test Before Deploying
```bash
python test-deployment.py
```

---

## 🔄 How to Update Your Web App

### Step 1: Make Changes
Edit your HTML, CSS, or JS files:
- `*.html` — Page structure and content
- `css/landing.css` — Main styles and design system
- `css/i18n.css` — Internationalization styles
- `css/info.css` — Info page styles
- `js/*.js` — Application logic

### Step 2: Test Locally
```bash
# Start the dev server
node dev-server.js

# Open in browser
# http://127.0.0.1:3000
```

### Step 3: Commit Changes
```bash
git add .
git commit -m "Description of your changes"
```

### Step 4: Deploy
```bash
# Push to deploy (Netlify auto-deploys on push)
git push origin main
```

---

## 📋 Deployment Options

### Option A: Git-Based (Recommended)
Netlify watches your Git repository and auto-deploys on push.

```bash
# Just push your changes
git push origin main
# Netlify builds and deploys automatically
```

### Option B: Manual Deploy via Netlify CLI
```bash
# Install Netlify CLI (one time)
npm install -g netlify-cli

# Deploy to production
netlify deploy --prod

# Deploy to staging
netlify deploy
```

### Option C: Drag & Drop
1. Go to [Netlify Dashboard](https://app.netlify.com)
2. Drag your project folder to the deploy area

---

## 🛡️ Pre-Deploy Checklist

- [ ] Test locally with `node dev-server.js`
- [ ] Check all pages load correctly
- [ ] Verify forms and interactive elements work
- [ ] Test on mobile/responsive view
- [ ] Run `python test-deployment.py`
- [ ] Back up database if making backend changes

---

## 🔧 Backend Updates

If you have a separate backend server:

```bash
# 1. Stop current backend
# 2. Update backend files in /backend folder
# 3. Restart backend
powershell .\launch-backend.ps1

# 4. Update API URL in js/config.js if needed
# 5. Deploy frontend changes
git push origin main
```

---

## 📁 Project Structure

```
swachlens/
├── index.html              # Landing page
├── admin.html              # Admin dashboard
├── employee.html           # Employee dashboard
├── user.html               # Citizen dashboard
├── login.html              # Citizen login
├── admin-login.html        # Admin/Employee login
├── register.html           # Registration
├── forgot-password.html    # Password recovery
├── admin-task-emp.html     # Admin task management
├── about.html              # About page
├── blog.html               # Blog
├── contact.html            # Contact
├── faq.html                # FAQ
├── help.html               # Help desk
├── api-docs.html           # API documentation
├── terms.html              # Terms of service
├── privacy.html            # Privacy policy
├── css/
│   ├── landing.css         # Main design system
│   ├── i18n.css            # Internationalization
│   └── info.css            # Info page styles
├── js/
│   ├── lang.js             # Language support
│   ├── config.js           # Configuration
│   ├── api.js              # API client
│   ├── ui.js               # Shared UI helpers
│   ├── admin.js            # Admin dashboard logic
│   ├── employee.js         # Employee dashboard logic
│   ├── user.js             # Citizen dashboard logic
│   ├── auth.js             # Authentication
│   ├── login.js            # Login logic
│   ├── admin-login.js      # Admin login logic
│   ├── landing.js          # Landing page logic
│   ├── hero-type.js        # Hero typewriter effect
│   └── state.js            # State management
├── backend/                # Backend server (if separate)
├── dev-server.js           # Local dev server
├── swachlens.db            # SQLite database
├── netlify.toml            # Netlify config
├── test-deployment.py      # Deployment test
└── launch-backend.ps1      # Backend launcher (Windows)
```

---

## 🎨 Design System

### Color Tokens (css/landing.css)
```css
--bg-primary: #0a0f1a      /* Main background */
--bg-secondary: #111827    /* Secondary background */
--bg-card: #1a2234         /* Card background */
--green-500: #22c55e       /* Primary green */
--green-400: #4ade80       /* Light green */
--purple-500: #a855f7      /* Primary purple */
--purple-400: #c084fc      /* Light purple */
--text-primary: #ffffff    /* White text */
--text-secondary: #94a3b8  /* Gray text */
--text-muted: #64748b      /* Muted text */
```

### Adding New Pages
1. Create `new-page.html`
2. Copy structure from existing page (e.g., `about.html`)
3. Add to footer links in all pages
4. Test locally before deploying

---

## 🐛 Troubleshooting

### Page not loading
- Check browser console for errors
- Verify file paths in HTML are correct
- Ensure dev server is running

### Styles not updating
- Hard refresh: `Ctrl + Shift + R` (Windows) or `Cmd + Shift + R` (Mac)
- Clear browser cache
- Check CSS file is linked correctly in HTML

### Backend connection issues
- Verify backend is running: `powershell .\launch-backend.ps1`
- Check API URL in `js/config.js`
- Check CORS settings on backend

---

## 📞 Support

- **Documentation:** Check `README.md` and `api-docs.html`
- **FAQ:** Visit `faq.html` on your deployed site
- **Contact:** Use `contact.html` form

---

**Last Updated:** September 2026
**Version:** 1.0.0
