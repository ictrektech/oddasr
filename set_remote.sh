#!/bin/bash
set -e

ORIGIN_URL="git@github.com:ictrektech/oddasr.git"
GH_URL="git@github.com:oddmeta/oddasr.git"

# 设置 origin
if git remote | grep -q "^origin$"; then
    git remote set-url origin "$ORIGIN_URL"
    echo "Updated remote 'origin'"
else
    git remote add origin "$ORIGIN_URL"
    echo "Added remote 'origin'"
fi

# 设置 gh
if git remote | grep -q "^gh$"; then
    git remote set-url gh "$GH_URL"
    echo "Updated remote 'gh'"
else
    git remote add gh "$GH_URL"
    echo "Added remote 'gh'"
fi