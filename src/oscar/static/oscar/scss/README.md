# CSS and Sass

Oscar uses Sass to build its CSS files.  Each of the 2 main CSS files has a
corresponding Sass file:

    styles.scss -> styles.css
    dashboard.scss -> dashboard.css

Oscar's CSS uses [Bootstrap 3.3.7](https://getbootstrap.com/docs/3.3/)

You can compile the CSS from the root of the project using a make target:
    
    make frontend
