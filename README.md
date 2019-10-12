## The Movie Database API Wrapper

For learning purposes. Just a wrapper to the apis.

#### Usage:

- First you need to obtain an api key [see here](https://www.themoviedb.org/documentation/api)
- Obtain a TMDBSession object, for a tv session you need  
  `session = session_factory('tv', apikey)`
- You will need a `Configuration` object for some operations 
  (eg. download poster images etc.)    
  `tmdbconf = Configuration.getconfig(session)`
- Now you can use the public methods available (or whatever you need to do)

#### Methods


