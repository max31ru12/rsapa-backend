# RSAPA Backend


## Setup local development environment

### Start and build containers

```shell
docker compose -f ./local.yml --build -d
```

For deployment the `HOST` environment variable should match the database service name ызусшашув шт `local.yml`.
For local development set `HOST` to `localhost`.


## Naming

### Branch naming

There are four name options for branches due to the GitFlow development:
1. `feature` - for features
2. `release`
3. `hotfix`
4. `bugfix`

### Commits naming

We use [conventional commits](https://www.conventionalcommits.org/en/v1.0.0/) to name our commits using the following special words:

- feat: (msg) - for new features
- fix: (msg) - for fixing bugs
- BREAKING CHANGE: (msg) - for
- ci: (msg)


## Main services


### App

Root URL of api must start with `api/` prefix. For example:

```
http://localhost:8000/api/users/1
```

### Media files storage

the storage is accessible via `MEDIA_PATH_NAME/file_name`. For example:

```
http://localhost:8000/api/media/photo.jpeg
```


### CI/CD
