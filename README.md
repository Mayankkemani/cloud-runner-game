# Cloud Runner 🏃 — Python Platformer Game

An original 2D platformer (Mario-style gameplay, original character/art) built with
**Pygame**, playable in the browser via **pygbag** (Pygame → WebAssembly), and
deployed automatically to AWS EC2 + Nginx using **GitHub Actions CI/CD**.

## Controls
- **Arrow keys / A, D** — move left/right
- **Space / W / Up arrow** — jump
- **R** — restart after Game Over / Win
- Jump on enemies to defeat them, collect coins, reach the flag to win.

---

## 1. Run locally (desktop, normal Python)

```bash
pip install -r requirements.txt
python main.py
```

A window will open — plain Pygame, no browser needed.

---

## 2. Build the browser (WebAssembly) version manually

This is what makes the game work as a **website** you can host on AWS.

```bash
pip install pygbag
python -m pygbag --build main.py
```

This creates a `build/web/` folder containing `index.html` and all the game
assets compiled to run in any modern browser — this is the folder that goes
onto your web server (S3 / EC2 + Nginx).

To preview it locally before deploying:
```bash
python -m pygbag main.py
```
Then open the URL it prints (usually `http://localhost:8000`).

---

## 3. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit - Cloud Runner game"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

---

## 4. CI/CD — Auto-deploy to AWS EC2 on every push

A ready-made GitHub Actions workflow is included at
`.github/workflows/deploy.yml`. On every push to `main`, it will:

1. Install pygbag
2. Build the WebAssembly web version (`build/web/`)
3. Copy those files to your EC2 instance over SSH
4. Move them into `/var/www/html/` (Nginx's web root) and restart Nginx

### One-time setup required (GitHub repo secrets)

Go to your GitHub repo → **Settings → Secrets and variables → Actions →
New repository secret**, and add:

| Secret name     | Value                                                            |
|------------------|-------------------------------------------------------------------|
| `EC2_HOST`       | Your EC2 public IP, e.g. `13.204.77.138`                          |
| `EC2_USER`       | `ubuntu` (or `ec2-user` for Amazon Linux)                          |
| `EC2_SSH_KEY`    | The **full contents** of your `.pem` private key file              |

To get the `.pem` contents:
```bash
cat your-key.pem
```
Copy everything, including the `-----BEGIN...-----` and `-----END...-----`
lines, into the `EC2_SSH_KEY` secret.

### Also make sure on EC2:
- Nginx is installed and running (`sudo systemctl status nginx`)
- The `ubuntu` user has permission to write to `/home/ubuntu/cloud-runner-deploy`
  (created automatically on first deploy)
- Security Group allows inbound **port 80 (HTTP)**
- Security Group allows inbound **port 22 (SSH)** from GitHub Actions
  (keep it open to `0.0.0.0/0` for SSH, or restrict to GitHub's IP ranges
  if you want tighter security)

### Trigger it
Just push any change to the `main` branch:
```bash
git add .
git commit -m "update game"
git push
```
GitHub Actions will build and deploy automatically — check the **Actions**
tab in your repo to watch it run. Once green, refresh
`http://<your-ec2-ip>` to play the latest version.

---

## Notes
- Game state (score, lives) resets each play session — no backend/database.
- All graphics are simple shapes drawn in code (no external image files),
  so there are no asset/licensing concerns.
- To change the level, edit the `build_level()` function in `main.py`.
