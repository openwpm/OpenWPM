export default [{
  input: 'index.js',
  output: {
    file: 'webextension/background.js',
    format: 'iife'
  }
}, {
  input: 'data/content.js',
  output: [
    {
      file: 'webextension/content.js',
      format: 'iife'
    }
  ]
}];
