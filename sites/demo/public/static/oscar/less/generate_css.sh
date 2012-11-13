#!/usr/bin/env bash

cd $(dirname $BASH_SOURCE)

echo "Generating styles.css"
lessc -x styles.less > ../css/styles.css

echo "Generating responsive.css"
lessc -x responsive.less > ../css/responsive.css

echo "Generating dashboard.css"
lessc -x dashboard.less > ../css/dashboard.css