# Django Oscar Information Page #

This repository contains the source for the [Django Oscar information page](http://tangentlabs.github.com/django-oscar/).

## Dependencies ##

[Jekyll](https://github.com/mojombo/jekyll/) is required. Follow the install instructions at the Jekyll [wiki](https://github.com/mojombo/jekyll/wiki/Install). You can install this via RubyGems: 

    sudo gem install jekyll

OSX users might need to update RubyGems:

    sudo gem update --system

## Building and Viewing ##

GitHub automatically builds Jekyll-based sites. If you want to make changes and edit locally, you'll need to install Jekyll (see above).

### Running a local server ###

cd into the `django-oscar` directory, and build by:

    jekyll --server --base-url=""
    
…where `--base-url` is an option to override the baseurl setting in `_config.yml`. This setting is used in the templates as the placeholder `{{ site.baseurl }}`

The generated site is available at `http://localhost:4000/`
