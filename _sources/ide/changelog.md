# Changelog

**Attention:** The docker recipes are (mostly) not version locked - rebuilding containers will likely result in differences in some library versions.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [unreleased]
### Release candidate
- enhancement: core/micropython/Dockerfile.template: add asyncio-mqtt
- bugfix: core/micropython/start-hook.sh: correctly set $HOST_IP


## [1.0.0] - 2022-01-07
### Initial release candidate
- see https://iot49.org
- really 1.0.0-rc1 ([rc1 spec not supported in balena.yml](https://github.com/balena-io/balena-cli/issues/2337))
