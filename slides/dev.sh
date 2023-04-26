#! /usr/bin/env nix-shell
#! nix-shell -i bash -p pandoc texlive.combined.scheme-medium librsvg
ls slides.md | entr pandoc slides.md -o slides.pdf
