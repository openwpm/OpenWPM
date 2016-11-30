// A second simple script
window.test_script_2_loaded = true;
console.log("test script 2 loaded");

var test = 1;

function test_function() {
  test = test + 1;
  console.log(test);
}

test_function();
test_function();
test_function();
