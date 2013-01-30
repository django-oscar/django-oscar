#!/usr/bin/env bash

cd $(dirname $BASH_SOURCE)

echo "Generating styles.css"
lessc styles.less > ../css/styles.css

echo "Generating responsive.css"
lessc responsive.less > ../css/responsive.css

echo "Generating dashboard.css"
lessc dashboard.less > ../css/dashboard.css
