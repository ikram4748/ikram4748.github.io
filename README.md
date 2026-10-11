# Portfolio website

Static site for M. Ikram Ullah, generated from `../cv/cv_data.yaml` (shared with the CVs) and `site_data.yaml`.

```bash
python build.py      # writes index.html and copies the CV PDFs from ../cv/output into cv/
python -m http.server 8000   # preview at http://localhost:8000
```

No framework: `index.html`, `assets/style.css`, `assets/app.js`. Light and dark themes, responsive from 320 px,
works without JavaScript; respects reduced-motion settings.
