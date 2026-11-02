# Putting the site on GitHub Pages

GitHub Pages hosts the site for free at an address like `https://<username>.github.io/`. Setup takes about 15 minutes. After that, publishing a change is one click.

The site is already built. GitHub only needs to serve the files in this folder.

## What you need

- A free GitHub account: <https://github.com/signup>. Your username is part of the web address, so choose it with that in mind.
- GitHub Desktop: <https://desktop.github.com>. It handles uploading without the command line. If you already use git, see [With the command line](#with-the-command-line) instead.

## 1. Choose the repository name

The repository name sets the address:

| Repository name | Site address |
|---|---|
| `<username>.github.io` (for example `kingguan.github.io`) | `https://kingguan.github.io/` |
| Anything else (for example `portfolio`) | `https://kingguan.github.io/portfolio/` |

Use `<username>.github.io` for the shortest address. All links in the site are relative, so either name works.

## 2. Upload the folder with GitHub Desktop

1. Open GitHub Desktop and sign in: **File > Options > Accounts > Sign in**.
2. Choose **File > Add local repository** and pick this folder (`CallumWebsite`).
3. GitHub Desktop says the folder isn't a repository yet. Click **create a repository**.
   - **Name**: the name from step 1.
   - Leave the other settings alone and click **Create repository**.
4. Click **Publish repository** at the top.
   - **Untick "Keep this code private."** On a free account, GitHub Pages only works with public repositories.
   - Click **Publish repository**. The upload is about 45 MB, so it can take a minute.

## 3. Turn on GitHub Pages

1. Open the repository on github.com. In GitHub Desktop, use **Repository > View on GitHub**.
2. Go to **Settings > Pages**. Pages is in the left sidebar under "Code and automation".
3. Under **Build and deployment**:
   - **Source**: Deploy from a branch
   - **Branch**: `main`, folder `/ (root)`, then **Save**.
4. Wait 1 to 2 minutes and refresh the page. The live address appears at the top: "Your site is live at …".

Open the address on a computer and on a phone to check it. This address is the link to share.

The **Actions** tab shows each deploy. A green tick means the site is live. A red cross means the deploy failed; open it to see why.

## 4. Publish changes later

1. Run `python tools/edit.py`, make your changes and press **Save**. Saving also rebuilds the pages.
2. Open GitHub Desktop. It lists the changed files.
3. Type a short summary at the bottom left, for example "New project: café", then click **Commit to main**.
4. Click **Push origin**.

The live site updates a minute or two later. If an old version still shows, refresh with Ctrl+F5, because browsers cache images.

If you edit `content/projects.json` by hand instead of using the editor, run `python tools/build.py` before committing. GitHub serves the built HTML, not the JSON.

## Optional: your own domain

To use an address like `callumzochowski.com`:

These steps are for a domain managed in Cloudflare.

1. In Cloudflare, open the domain and go to **DNS > Records**. Add these records with **Proxy status** set to **DNS only** (grey cloud), not Proxied (orange cloud):

   | Type | Name | Content |
   |---|---|---|
   | A | `@` | `185.199.108.153` |
   | A | `@` | `185.199.109.153` |
   | A | `@` | `185.199.110.153` |
   | A | `@` | `185.199.111.153` |
   | CNAME | `www` | `<username>.github.io` |

   Delete any other `A`, `AAAA` or `CNAME` records for `@` or `www` first, such as a parking page.
2. In the repository, go to **Settings > Pages > Custom domain**, enter the domain (for example `callumzochowski.com`) and click **Save**. GitHub then adds a `CNAME` file to the repository. In GitHub Desktop, click **Fetch origin**, then **Pull origin**, so your copy has that file too.
3. Wait for the DNS check to pass, then tick **Enforce HTTPS**. This usually takes minutes, but can take up to a day. GitHub issues the security certificate itself.

Keep the records on **DNS only**. With the orange cloud on, GitHub can't issue its certificate. If you turn the proxy on later anyway, set Cloudflare's **SSL/TLS** mode to **Full**. The **Flexible** mode makes the site redirect in an endless loop.

Optionally, in your GitHub account (not the repository), go to **Settings > Pages > Add a domain** and add the TXT record it shows in Cloudflare. This verifies that you own the domain, so no one else's GitHub site can claim it.

## Good to know

- **Everything in the repository is public.** That includes the editor in `tools/` and `content/projects.json`. Neither contains anything private. The editor page can be opened online, but it can't save anything there, because saving needs `edit.py` running on your computer.
- **What's left out**: `.gitignore` keeps the editor's backup file and Python's cache files out of the repository.
- **Upper and lower case matter online.** Windows treats `Photo.jpg` and `photo.jpg` as the same file, but GitHub Pages doesn't. Images added through the editor are fine. If you rename image files by hand, the names in `projects.json` must match exactly.
- **Size limits**: each file must be under 100 MB and the whole site under 1 GB. The site is about 45 MB now.
- **Before you share the link**: get Callum's approval, and get permission from Azamat Khairov to host the reference image on the UE Style Study page. His ArtStation page says "© All rights reserved".

## With the command line

From inside this folder:

```
git init -b main
git add .
git commit -m "Portfolio site"
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

Create the empty repository on github.com first, at **New repository**. Make it public and don't add a README. Then follow [step 3](#3-turn-on-github-pages).

To publish changes later:

```
git add .
git commit -m "Describe the change"
git push
```
