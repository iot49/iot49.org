# Docker App

*ide49* is a docker application, consisting of several containers, loosely coupled via shared data and a dedicated internal network. The all share a single Linux kernel, but each container has its own copy of programs, avoiding incompatibilities, e.g. due to different libraries.

Customization - both modifying existing features and adding new ones - can be done easily, right from within *ide49*. 

This section gives a brief overview of the *ide49* docker application and specific [instructions](app/customize.ipynb) to customize it. In-depth documentation is available at the [Docker](https://docs.docker.com/) and [Balena](https://www.balena.io/docs) websites.