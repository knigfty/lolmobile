## Running locally

Serve the repository root over HTTP. For example, if Python is installed:

```powershell
python -m http.server 8000
```

Open `http://localhost:8000/`. The Python server does not apply `vercel.json`; use `http://localhost:8000/settings/` to open settings directly. The arena's `/settings` link may be redirected to that directory by the local server.

Use a browser with WebGL and JavaScript module/import-map support. Internet access is required to fetch Three.js: the import map pins both `three` and `three/addons/` to version `0.165.0` on jsDelivr. Opening the HTML with `file://` can prevent model or module loading.

For static hosting, publish the repository root with its asset directories intact. Hosts other than Vercel need an equivalent `/settings` route or directory handling. Navigation uses root-relative URLs, so deployment beneath a URL subdirectory requires changes to the links and routing.