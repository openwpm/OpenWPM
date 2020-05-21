function interactWithTestObjects() {

  /*
    * Interact with partially existing object instrumented non-recursively
    */

  // get object
  console.log("partiallyExisting",window.partiallyExisting);

  // call object as method
  try {
    window.partiallyExisting('hello', {'world': true});
  } catch (e) {
    console.log("call object as method - caught exception: ", e);
  }

  // get and set existingProp
  try {
    console.log("existingProp before set", window.partiallyExisting.existingProp);
  } catch (e) {
    console.log("existingProp before set - caught exception: ", e);
  }
  window.partiallyExisting.existingProp = 'blah1';
  try {
    console.log("existingProp after set", window.partiallyExisting.existingProp);
  } catch (e) {
    console.log("existingProp after set - caught exception: ", e);
  }

  // get and set nonExistingProp1 (data property 1)
  console.log("nonExistingProp1 before set", window.partiallyExisting.nonExistingProp1);
  window.partiallyExisting.nonExistingProp1 = 'blah1';
  console.log("nonExistingProp1 after set", window.partiallyExisting.nonExistingProp1);

  // call non-existing object method
  try {
    window.partiallyExisting.nonExistingMethod1('hello', {'world': true});
  } catch (e) {
    console.log("call object method - caught exception: ", e);
  }

}