# Vendored: Paged.js

| | |
|---|---|
| File | `paged.polyfill.js` |
| Project | Paged.js, https://gitlab.coko.foundation/pagedjs/pagedjs |
| Version | 0.4.3 (npm `pagedjs@0.4.3`, `dist/paged.polyfill.js`) |
| License | MIT, see `paged.LICENSE.md` |
| SHA-256 | `f59f361802416c770d549a647958649af2cf6601999924bc00e4f507dad5269f` |

`scripts/pdf/build.mjs` loads this self-contained browser bundle into headless Chromium to paginate the
book. It is vendored instead of installed from npm because every published `pagedjs` version, including
the 0.5 betas, declares runtime dependencies on the deprecated `@babel/polyfill` and, through it,
`core-js@2`. The bundle never loads them, but `npm ci` warned about both on every install.

## Updating

1. Download the new release: `npm pack pagedjs@<version>` and extract `package/dist/paged.polyfill.js`
   and `package/LICENSE.md`.
2. Replace both files here, keeping the `@license` header at the top of the bundle.
3. Update the version and SHA-256 above (`shasum -a 256 paged.polyfill.js`).
4. Run `make pdf` and inspect the contents page, a chapter opening and a page with a wide table.
