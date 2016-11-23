// We don't know the order the content scripts will load
// so let's try to remove the attributes now (if they already exist)
// or register an event handler if they don't.
console.log("BEFORE navigator.webdriver: ", navigator.webdriver);
console.log("BEFORE webdriver in navigator: ", !!("webdriver" in navigator));
console.log("BEFORE documentElement attribute webdriver: ", document.documentElement.getAttribute("webdriver"));

if ("webdriver" in navigator) {
  document.documentElement.removeAttribute("webdriver");
  delete window.navigator["webdriver"];
  console.log("AFTER IMMEDIATE navigator.webdriver: ", navigator.webdriver);
  console.log("AFTER IMMEDIATE webdriver in navigator: ", !!("webdriver" in navigator));
  console.log("AFTER IMMEDIATE documentElement attribute webdriver: ", document.documentElement.getAttribute("webdriver"));
} else {
  document.addEventListener("DOMAttrModified", function(ev) {
    document.documentElement.removeAttribute("webdriver");
    if ("webdriver" in navigator) {
      delete window.navigator["webdriver"];
    }
    document.documentElement.removeAttribute("webdriver");
    console.log("AFTER ME navigator.webdriver: ", navigator.webdriver);
    console.log("AFTER ME webdriver in navigator: ", !!("webdriver" in navigator));
    console.log("AFTER ME documentElement attribute webdriver: ", document.documentElement.getAttribute("webdriver"));
  }, {once: true});
}
