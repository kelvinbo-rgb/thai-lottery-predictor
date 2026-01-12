# Deploy Thai Lottery to Koyeb

1. **Push Changes to GitHub**:
   - Open **GitHub Desktop**.
   - Commit the new `Dockerfile` and `.dockerignore`.
   - Push to `origin`.

2. **Deploy on Koyeb**:
   - Go to [Koyeb Console](https://app.koyeb.com/).
   - Click **Create App** (or Service).
   - **Source**: GitHub.
   - **Repository**: Select `thai-lottery-predictor`.
   - **Builder**: **Dockerfile** (It should auto-detect, but force Dockerfile if asked).
   - **Port**: Change to **8000** (Important! Streamlit is configured to 8000 in Dockerfile).
   - Click **Deploy**.

3. **Verify**:
   - Wait for deployment to switch to "Healthy".
   - Open the App URL.
