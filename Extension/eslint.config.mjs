/*
This ESLint config aims to work with both
the JavaScript and the TypeScript parts of the
codebase.
*/

import js from "@eslint/js";
import tseslint from "typescript-eslint";
import prettier from "eslint-plugin-prettier/recommended";
import jsdoc from "eslint-plugin-jsdoc";
import unicorn from "eslint-plugin-unicorn";
import importPlugin from "eslint-plugin-import";
import html from "eslint-plugin-html";
import json from "eslint-plugin-json";
import noUnsanitized from "eslint-plugin-no-unsanitized";
import globals from "globals";

export default tseslint.config(
  // Global ignores
  {
    ignores: [
      "bundled/feature.js",
      "bundled/content.js",
      "bundled/privileged/sockets/bufferpack.js",
      "eslint.config.mjs",
      "build/",
      "dist/",
      "node_modules/",
    ],
  },

  // Base config for all JS files
  js.configs.recommended,

  // Base rules for all files
  {
    languageOptions: {
      globals: {
        ...globals.node,
        ...globals.es2021,
        ...globals.browser,
        ...globals.webextensions,
      },
    },
    plugins: {
      html,
      import: importPlugin,
      jsdoc,
      json,
      unicorn,
      "no-unsanitized": noUnsanitized,
    },
    rules: {
      "arrow-parens": ["off", "always"],
      "brace-style": ["off", "off"],
      "comma-dangle": "off",
      complexity: "off",
      "constructor-super": "error",
      "eol-last": "off",
      eqeqeq: ["warn", "smart"],
      "guard-for-in": "warn",
      "id-denylist": "warn",
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
      "no-fallthrough": "off",
      "no-invalid-this": "off",
      "no-irregular-whitespace": "off",
      "no-multiple-empty-lines": "off",
      "no-new-func": "error",
      "no-new-wrappers": "error",
      "no-redeclare": "error",
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
  },

  // Privileged extension scripts
  {
    files: ["bundled/privileged/**/*.js"],
    languageOptions: {
      globals: {
        AppConstants: "readonly",
        console: "readonly",
        Cu: "readonly",
        Ci: "readonly",
        Cc: "readonly",
        Cr: "readonly",
        ChromeUtils: "readonly",
        ChromeWorker: "readonly",
        extensions: "readonly",
        ExtensionAPI: "readonly",
        ExtensionCommon: "readonly",
        ExtensionUtils: "readonly",
        IOUtils: "readonly",
        MatchGlob: "readonly",
        MatchPattern: "readonly",
        MatchPatternSet: "readonly",
        Services: "readonly",
        StructuredCloneHolder: "readonly",
        OS: "readonly",
        PathUtils: "readonly",
        XPCOMUtils: "readonly",
      },
    },
  },

  // TypeScript files
  ...tseslint.configs.recommended.map((config) => ({
    ...config,
    files: ["**/*.ts"],
  })),
  {
    files: ["**/*.ts"],
    languageOptions: {
      parserOptions: {
        project: "tsconfig.json",
        sourceType: "module",
      },
    },
    rules: {
      "@typescript-eslint/adjacent-overload-signatures": "error",
      "@typescript-eslint/array-type": [
        "error",
        {
          default: "array",
        },
      ],
      "@typescript-eslint/no-restricted-types": [
        "error",
        {
          types: {
            Object: {
              message: "Avoid using the `Object` type. Did you mean `object`?",
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
              message: "Avoid using the `Number` type. Did you mean `number`?",
            },
            String: {
              message: "Avoid using the `String` type. Did you mean `string`?",
            },
            Symbol: {
              message: "Avoid using the `Symbol` type. Did you mean `symbol`?",
            },
          },
        },
      ],
      "@typescript-eslint/consistent-type-assertions": "off",
      "@typescript-eslint/dot-notation": "error",
      "@typescript-eslint/no-empty-function": "warn",
      "@typescript-eslint/no-empty-object-type": "error",
      "@typescript-eslint/no-explicit-any": "off",
      "@typescript-eslint/no-misused-new": "error",
      "@typescript-eslint/no-namespace": "error",
      "@typescript-eslint/no-shadow": [
        "off",
        {
          hoist: "all",
        },
      ],
      "@typescript-eslint/no-this-alias": "error",
      "@typescript-eslint/no-unused-expressions": "warn",
      "@typescript-eslint/no-use-before-define": "off",
      "@typescript-eslint/prefer-for-of": "warn",
      "@typescript-eslint/prefer-function-type": "error",
      "@typescript-eslint/prefer-namespace-keyword": "error",
      "@typescript-eslint/triple-slash-reference": [
        "error",
        {
          path: "always",
          types: "prefer-import",
          lib: "always",
        },
      ],
      "@typescript-eslint/unified-signatures": "error",
      "no-undef": "off",
      "no-unused-vars": "off",
      "@typescript-eslint/no-unused-vars": [
        "error",
        { argsIgnorePattern: "^_" },
      ],
    },
  },

  // Prettier must be last to override formatting rules
  prettier,
);
