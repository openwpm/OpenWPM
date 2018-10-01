import commonjs from 'rollup-plugin-commonjs';
import nodeResolve from 'rollup-plugin-node-resolve';
import builtins from 'rollup-plugin-node-builtins';
import globals from 'rollup-plugin-node-globals';

const plugins = [
  commonjs(),
  nodeResolve({
    preferBuiltins: true,
  }),
  globals(),
  builtins(),
]

export default [{
  input: 'index.js',
  output: {
    file: 'webextension/background.js',
    format: 'iife',
    globals: {
      'ws': 'WebSocket',
      'xmlhttprequest-ssl': 'XMLHttpRequest',
    }
  },
  external: ['ws', 'xmlhttprequest-ssl'],
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
