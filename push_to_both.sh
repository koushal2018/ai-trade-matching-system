#!/bin/bash

echo "Pushing to GitLab..."
git push origin main

echo "Pushing to GitHub (ai-trade-reconciliation)..."
git push github main

echo "Successfully pushed to both GitLab and GitHub!"