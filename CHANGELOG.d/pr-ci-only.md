chore: run CI only for pull requests

Removes redundant post-merge CI runs while leaving the independent release and image
publication workflow triggered by pushes to `main`.
