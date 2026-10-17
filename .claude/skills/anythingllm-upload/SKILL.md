---
name: anythingllm-upload
description: Use when the user wants to upload, add, sync, or embed notes/Markdown files into their self-hosted AnythingLLM, put a note into an AnythingLLM workspace, or create/list AnythingLLM workspaces.
---

# AnythingLLM Upload

Upload notes from this vault into the user's AnythingLLM with the bundled `upload.py`. It skips notes already in the workspace, reuses an up-to-date stored copy instead of uploading again, and swaps out the old copy when the local note was edited.

Config: `~/.anythingllm.json` → `{"url": "http://localhost:8085", "api_key": "..."}`. The env vars `ANYTHINGLLM_URL` and `ANYTHINGLLM_API_KEY` override it. Keep this file outside the repo; never write the key or the config into this repo, because the repo is pushed to GitHub. If the script reports `Missing url/api_key`, ask the user for the server URL and a key from **Settings → Tools → Developer API**, then write the file.

## Steps

1. List the workspaces:
   `python .claude/skills/anythingllm-upload/upload.py list` → `slug | name | doc count`
2. Choose the workspace by the note's topic, comparing it with the workspace **names** (the slug can differ, e.g. slug `my-workspace` = "Investment"). The user wants as **few workspaces as possible**: use an existing workspace whenever its topic is broad enough. Create one only when no workspace fits, and give it a broad topic name that later notes can share:
   `python .claude/skills/anythingllm-upload/upload.py create "Name"` → prints the new slug
3. Upload one or more files:
   `python .claude/skills/anythingllm-upload/upload.py upload <slug> <file.md> [more.md ...]`
4. Report each file's result line (`ADD … uploaded` / `ADD … reused stored copy` / `SKIP … already in` / `FAILED`) and which workspace you used.

For a whole folder, pass several files to one call, not one call per file. Exclude `.claude/`, `.agents/` and `index.md`.

## Common mistakes

| Mistake | What happens |
|---|---|
| Passing the slug in the wrong case (`My-workspace`) | The API returns an empty workspace and no error. The script stops with `No workspace with slug`. Copy the slug exactly from `list`. |
| Raw `curl` to `/document/upload` | Uploading the same note again creates a duplicate copy. Use the script, which checks for existing copies first. |
| Using the workspace name as the slug | Use the slug that `list` prints. |
| Expecting the images in a note to come along | Only the Markdown text is embedded. The images in `xiaohongshu-downloads/` and `twitter-downloads/` are not uploaded. |

Stored filenames lose their Chinese characters (`__.md-<uuid>.json`). The document titles keep them, and the script matches on titles.
