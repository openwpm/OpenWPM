/* eslint-env node */
/*
This ESLint config aims to work with both
the JavaScript and the TypeScript parts of the
codebase.
*/

module.exports = {
  root: true,
  env: {
    node: true,
    es6: true,
    webextensions: true,
    browser: true,
  },
  parser: "@babel/eslint-parser",
  extends: ["prettier", "eslint:recommended"],
  ignorePatterns: [
    "bundled/feature.js",
    "bundled/content.js",
    "bundled/privileged/sockets/bufferpack.js" /** This is a file we just copied in  */,
    "build/",
    "dist/",
    "node_modules/",
  ],
  plugins: [
    "eslint-plugin-html",
    "eslint-plugin-import",
    "eslint-plugin-jsdoc",
    "eslint-plugin-json",
    "eslint-plugin-unicorn",
    "eslint-plugin-mozilla",
    "eslint-plugin-no-unsanitized",
  ],
  rules: {
    "arrow-parens": ["off", "always"],
    "brace-style": ["off", "off"],
    "comma-dangle": "off",
    complexity: "off",
    "constructor-super": "error",
    "eol-last": "off",
    eqeqeq: ["warn", "smart"],
    "guard-for-in": "warn",
    "id-blacklist": "warn",
    "id-match": "warn",
    "import/no-extraneous-dependencies": ["error"],
    "import/no-internal-modules": "error",
    "jsdoc/check-alignment": "error",
    "jsdoc/check-indentation": "error",
    "jsdoc/tag-lines": [
      "error",
      "any",
      {
        startLines: 1,
      },
    ],
    "linebreak-style": "off",
    "max-classes-per-file": ["error", 1],
    "max-len": "off",
    "new-parens": "off",
    "newline-per-chained-call": "off",
    "no-bitwise": "warn",
    "no-caller": "error",
    "no-cond-assign": "error",
    "no-debugger": "error",
    "no-duplicate-case": "error",
    "no-duplicate-imports": "error",
    "no-empty": "warn",
    "no-eval": "error",
    "no-extra-bind": "error",
    "no-extra-semi": "off",
    "no-fallthrough": "off",
    "no-invalid-this": "off",
    "no-irregular-whitespace": "off",
    "no-multiple-empty-lines": "off",
    "no-new-func": "error",
    "no-new-wrappers": "error",
    "no-redeclare": "error",
    "no-return-await": "error",
    "no-sequences": "error",
    "no-sparse-arrays": "error",
    "no-template-curly-in-string": "error",
    "no-throw-literal": "error",
    "no-trailing-spaces": "off",
    "no-undef-init": "error",
    "no-underscore-dangle": "warn",
    "no-unsafe-finally": "error",
    "no-unused-labels": "error",
    "no-unused-vars": ["error", { argsIgnorePattern: "^_" }],
    "no-var": "error",
    "object-shorthand": "error",
    "one-var": ["warn", "never"],
    "prefer-const": "error",
    "prefer-object-spread": "error",
    "quote-props": "off",
    radix: "error",
    "space-before-function-paren": "off",
    "space-in-parens": ["off", "never"],
    "spaced-comment": [
      "error",
      "always",
      {
        markers: ["/"],
      },
    ],
    "unicorn/prefer-ternary": "error",
    "use-isnan": "error",
    "valid-typeof": "off",
  },
  overrides: [
    {
      files: ["bundled/privileged/**"],
      env: {
        es2022: true,
        "mozilla/browser-window": true,
        "mozilla/privileged": true,
      },
      /** See https://firefox-source-docs.mozilla.org/toolkit/components/extensions/webextensions/basics.html#globals-available-in-the-api-scripts-global */
      globals: [
        "AppConstants",
        "console",
        "Cu",
        "Ci",
        "Cc",
        "Cr",
        "ChromeWorker",
        "extensions",
        "ExtensionAPI",
        "ExtensionCommon",
        "ExtensionUtils",
        "ExtensionUtils",
        "MatchGlob",
        "MatchPattern",
        "MatchPatternSet",
        "Services",
        "StructuredCloneHolder",
        "OS",
        "XPCOMUtils",
      ].reduce((acc, e) => {
        acc[e] = "readonly";
        return acc;
      }, {}),
    },
    {
      files: ["*.ts"],
      parser: "@typescript-eslint/parser",
      parserOptions: {
        project: "tsconfig.json",
        sourceType: "module",
      },
      plugins: ["@typescript-eslint"],
      rules: {
        "@typescript-eslint/adjacent-overload-signatures": "error",
        "@typescript-eslint/array-type": [
          "error",
          {
            default: "array",
          },
        ],
        "@typescript-eslint/ban-types": [
          "error",
          {
            types: {
              Object: {
                message:
                  "Avoid using the `Object` type. Did you mean `object`?",
              },
              Function: {
                message:
                  "Avoid using the `Function` type. Prefer a specific function type, like `() => void`.",
              },
              Boolean: {
                message:
                  "Avoid using the `Boolean` type. Did you mean `boolean`?",
              },
              Number: {
                message:
                  "Avoid using the `Number` type. Did you mean `number`?",
              },
              String: {
                message:
                  "Avoid using the `String` type. Did you mean `string`?",
              },
              Symbol: {
                message:
                  "Avoid using the `Symbol` type. Did you mean `symbol`?",
              },
            },
          },
        ],
        "@typescript-eslint/consistent-type-assertions": "off",
        "@typescript-eslint/dot-notation": "error",
        "@typescript-eslint/indent": "off",
        "@typescript-eslint/member-delimiter-style": [
          "off",
          {
            multiline: {
              delimiter: "none",
              requireLast: true,
            },
            singleline: {
              delimiter: "semi",
              requireLast: false,
            },
          },
        ],
        "@typescript-eslint/no-empty-function": "warn",
        "@typescript-eslint/no-empty-interface": "error",
        "@typescript-eslint/no-explicit-any": "off",
        "@typescript-eslint/no-misused-new": "error",
        "@typescript-eslint/no-namespace": "error",
        "@typescript-eslint/no-parameter-properties": "off",
        "@typescript-eslint/no-shadow": [
          "off",
          {
            hoist: "all",
          },
        ],
        "@typescript-eslint/no-this-alias": "error",
        "@typescript-eslint/no-unused-expressions": "warn",
        "@typescript-eslint/no-use-before-define": "off",
        "@typescript-eslint/no-var-requires": "error",
        "@typescript-eslint/prefer-for-of": "warn",
        "@typescript-eslint/prefer-function-type": "error",
        "@typescript-eslint/prefer-namespace-keyword": "error",
        "@typescript-eslint/quotes": "off",
        "@typescript-eslint/semi": ["off", null],
        "@typescript-eslint/triple-slash-reference": [
          "error",
          {
            path: "always",
            types: "prefer-import",
            lib: "always",
          },
        ],
        "@typescript-eslint/type-annotation-spacing": "off",
        "@typescript-eslint/unified-signatures": "error",
        "no-undef": "off",
        "no-unused-vars": "off",
        "@typescript-eslint/no-unused-vars": [
          "error",
          { argsIgnorePattern: "^_" },
        ],
      },
    },
  ],
};
