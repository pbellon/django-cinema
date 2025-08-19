# Notes

I initially started by bootstrapping the project using `django-admin` but pivoted to rely on
[django-startproject](https://github.com/jefftriplett/django-startproject) to have a working setup
for docker, docker-compose & uv because I struggled making it work properly. I intend to clean
it for every part I don't think necessary / not clear to me.

## Plan
- [x] setup django project with docker, docker-compose, and postgresql
- [ ] create base models
    - [ ] Author (aka director)
    - [ ] Movie
    - [ ] Spectator
    - [ ] SpectatorMovieEvaluation
    - [ ] SpectatorAuthorEvaluation
- [ ] create proper admin on every model
- [ ] create custom list filters
    - [ ] movie release date
    - [ ] movie evaluation
    - [ ] movie status
    - [ ] author having at least one movie
- [ ] create tmdbpopulate command and use tmdb API to populate models
- [ ] Implement API
    - [ ] Author
        - *list all authors
        - get single author
        - put author
        - delete author (only if no related movie)