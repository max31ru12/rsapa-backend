# RSAPA Backend


## Setup local development environment

### Start and build containers

```shell
docker compose -f ./local.yml --build -d
```


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
