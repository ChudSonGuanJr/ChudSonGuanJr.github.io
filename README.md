# Callum Żochowski portfolio

A static portfolio site for GitHub Pages. No framework and no server: the HTML is pre-built and committed.

## Publish on GitHub Pages

1. Create a GitHub repository and push this folder to it.
   - Name it `<username>.github.io` to serve the site at `https://<username>.github.io/`.
   - Any other name serves it at `https://<username>.github.io/<repo>/`. All links are relative, so both work.
2. In the repository, open **Settings > Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, then `main` and `/ (root)`, and save.

The site goes live a minute or two later. For the full walkthrough, see [GITHUB_SETUP.md](GITHUB_SETUP.md). It covers GitHub Desktop with no command line, publishing updates and adding a custom domain.

## Edit mode

`edit.bat` (double-click) or `python tools/edit.py` opens a local control panel for the whole site: colours, fonts, site details, about text, experience and tools, plus every project's text, credits, links, sections and images. You can add projects and sections, upload images, drag anything into order, move images between projects, pick tiles, banners, the header and the home page button images with live previews, join two matching shots into a drag slider with Pair, and give a project's sections their own thumbnail pages with left and right arrows. Press **Save** when you're done. Save updates `content/projects.json` and rebuilds the pages; the previous version is kept as `content/projects.backup.json`. Removed images stay in `assets/img/`, so an image can be restored by adding it back to the JSON. Press Ctrl+C in the terminal to stop. Nothing goes live until you commit and push. To drop edit mode for good, delete `tools/edit.py` and `tools/editor.html`.

## Update the content

Everything lives in [content/projects.json](content/projects.json):

- `site`: name, title, about text, experience, tools, hero images and `email`. Set `email` to replace the ArtStation contact button with a mail link.
- `projects`: one entry per project, in display order. `thumbnail` is the square home page tile and `cover` is the wide banner on the project page. Put images in `assets/img/<slug>/` and list them under `sections`.

Then rebuild and commit the result:

```
pip install pillow
python tools/build.py
```

Preview locally with `python -m http.server` and open <http://localhost:8000>.
