# Digital Hospitals project monorepo

**Authors**: Yin Chi Chan; Anandarup Mukherjee; Rohit Krishnan <br/>
&copy; 2024 Digital Hospitals group, Institute for Manufacturing, University of Cambridge

This repo is to consolidate all subprojects of the Digital Hospital project.

## Git config

Add the following to your git config:

```bash
git config --global alias.root 'rev-parse --show-toplevel'
```

## Branch protection

The `main` branch of this monorepo is protected. If you accidentally commit to `main` you will not be able to `git push`.
To resolve this, execute the following script:

```bash
git commit -a -m "Saving my work, just in case"
git branch my-new-branch
git fetch origin
git reset --hard origin/main
```
