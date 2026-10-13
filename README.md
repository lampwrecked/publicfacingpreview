# publicfacingpreview — load optimizations

Same page, same morphing portrait, far fewer downloads.

## What changed in `index.html`

| Before | After |
|---|---|
| 384 full-size PNGs requested per visit (3 per layer at once, then the other 360 two seconds later) | 8 requests for the first face, then a queue that grows each layer to 12 images (96 total) with 4 downloads in flight at a time |
| All 8 layers' first images race 24 other downloads | Queue round-robins so every layer gets its first image before any layer gets a second |
| Keeps downloading and animating in a background tab | Pauses both while the tab is hidden, resumes when it's visible |
| Ignores Data Saver | Caps at 3 images per layer when the visitor has Data Saver on |
| `splash.jpg` referenced in CSS but not in the repo (a 404 on every load) | Removed |
| Cormorant Garamond in 4 styles, 2 unused | Only the weights the page uses |
| First image waits on a cold connection to R2 | `<link rel="preconnect">` to the R2 host |
| `img.src` swaps decode on the main thread | Images decode off-thread before the swap |

Nothing about the signup form or the API changed.

## Two more wins that need the bucket

These are where the biggest remaining savings are, and they need your trait files rather than the HTML.

**1. Smaller images.** The window is at most 560 CSS px wide, so a 1200 px WebP looks identical on a 2x screen and is a fraction of a full-res PNG. `tools/resize-traits.py` makes a parallel folder of them:

```
pip install pillow
python3 tools/resize-traits.py /path/to/traits ./web --width 1200
```

Upload `./web` to the bucket under a `web/` prefix, then in `index.html` set `BASE` to `https://pub-….r2.dev/web/` and `EXT` to `webp`.

**2. Cache headers on R2.** Public R2 objects send no `Cache-Control` unless the object was uploaded with one, so browsers re-check every image on every visit. Upload (or re-upload) the trait files with:

```
Cache-Control: public, max-age=31536000, immutable
```

With rclone that's `--header-upload "Cache-Control: public, max-age=31536000, immutable"`; with wrangler it's `--cache-control`. The `vercel.json` here does the same for anything served from this repo.

## Tunables

At the top of the script in `index.html`:

- `POOL_TARGET` — images per layer to keep (default 12; 3 under Data Saver)
- `CONCURRENCY` — downloads in flight at once (default 4)
- `INTERVAL_MS` — ms between face swaps (unchanged, 1000)
