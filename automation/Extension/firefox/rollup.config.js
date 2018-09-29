import commonjs from 'rollup-plugin-commonjs';
import nodeResolve from 'rollup-plugin-node-resolve';

const plugins = [
  commonjs({
    namedExports: {
      'bufferpack': [ 'pack', 'unpack' ]
    }
  }),
  nodeResolve(),
]

export default [{
  input: 'index.js',
  output: {
    file: 'webextension/background.js',
    format: 'iife'
  },
  plugins
}, {
  input: 'data/content.js',
  output: [
    {
      file: 'webextension/content.js',
      format: 'iife'
    }
  ],
  plugins
}];
