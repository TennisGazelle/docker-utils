# docker-utils
utilities for managing docker images

# docker-merger.py
Not supposed to have two different base images in the same dockerfile? Of course.
Is having multistage builds a better idea? Perhaps.
But does that mean that the absolute need will ever not arise? NO.
If you want to create that unholy union:

```bash
usage: dockerfile-merger.py [-h] [-c] i i

Produce Dockerfile that merges two docker base images

positional arguments:
  i                     images to merge

optional arguments:
  -h, --help            show this help message and exit
  -c, --check-compatibility
                        print out the base ADD cmd of each image

```

expected behavior (assuming you already have `golang:alpine` and `python:alpine` prepulled on your local with `docker pull golang:alpine python:alpine`)

```bash
./docker-merger.py golang:alpine python:alpine
INFO:root:golang:alpine image found: sha256:e04879bf1b7fb06885d0f88d3870584dd1ee21e9301e4fd32da7e4666e54aa6b
INFO:root:python:alpine image found: sha256:fe3ef29c73f3ebaffa0dead8391b75be18894d771a841c28ca1140fec358c5e2
INFO:root:comparing the ADD cmds for docker images: python:alpine and golang:alpine
INFO:root:python:alpine: 
        - ADD file:a86aea1f3a7d68f6ae03397b99ea77f2e9ee901c5c59e59f76f93adbb4035913 in / 
INFO:root:golang:alpine: 
        - ADD file:a86aea1f3a7d68f6ae03397b99ea77f2e9ee901c5c59e59f76f93adbb4035913 in / 
```

produces a dockerfile that adds the raw layer comands of the second into the first:

```Dockerfile
FROM golang:alpine
ENV PATH=/usr/local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV LANG=C.UTF-8
# ... go stuff...
```
