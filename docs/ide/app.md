# Docker App

*ide49* is a docker application, consisting of several containers, loosely coupled via shared data and a dedicated internal network. Each has its own copy of Linux, avoiding incompatibilites, e.g. from different libraries.

Customization - both modifying existing features and adding new ones - can be done easily, right from within *ide49*. 

This section gives a brief overview of the *ide49* docker application and specific [instructions](app/customize.ipynb) to customize it. In-depth documentation is available at the [Docker](https://docs.docker.com/) and [Balena](https://www.balena.io/docs) websites.