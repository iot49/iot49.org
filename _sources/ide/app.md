# Docker App

*ide49* is a docker application, consisting of several containers, loosely coupled via shared data and a dedicated internal network. Each has its own copy of Linux, avoiding incompatibilites, e.g. from different libraries.

Customization - both modifying existing features and adding new ones, e.g. database support or specialized or proprietary tools needed by your project - can be done easily and safely, right from within *ide49*. 

This chapter describes the *ide49* docker application and specific [instructions](app/customize.ipynb) to customize it.