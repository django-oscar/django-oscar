/* Handles the page being scrolled by ensuring the navigation is always in
 * view.
 */
function handleScroll(){

  // check that this is a relatively modern browser
  if (window.XMLHttpRequest){

    // determine the distance scrolled down the page
    var offset = window.pageYOffset
               ? window.pageYOffset
               : document.documentElement.scrollTop;

    // set the appropriate class on the navigation
    document.getElementById('nav').className =
        (offset > 180 ? 'fixed' : '');

  }

}

// add the scroll event listener
if (window.addEventListener){
  window.addEventListener('scroll', handleScroll, false);
}else{
  window.attachEvent('onscroll', handleScroll);
}

$.scrollTo( '#section', 800, {easing:'elasout'} );