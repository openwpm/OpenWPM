// A function in an external script
function js_check_navigator() {
    console.log(window.navigator.userAgent);
    var foo = eval("window.navigator.platform");
}

// call the above function
js_check_navigator();

// use eval
var bar = eval("window.navigator.buildID");

//use Function
new Function("window.navigator.appVersion")();
