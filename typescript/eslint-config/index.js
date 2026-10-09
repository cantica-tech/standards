// cantica-tech TypeScript lint standard (ESLint flat config).
// A consumer's eslint.config.mjs:
//   import standard from "@cantica-tech/eslint-config";
//   export default [...standard({ tsconfigRootDir: import.meta.dirname }), /* its own ratchet */];
import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import tseslint from "typescript-eslint";

export default function standard({ tsconfigRootDir, ignores = [] } = {}) {
  return tseslint.config(
    { ignores: ["**/dist/**", "**/out/**", "**/node_modules/**", "**/*.js", "**/*.cjs", "**/*.mjs", ...ignores] },
    js.configs.recommended,
    ...tseslint.configs.strictTypeChecked,
    ...tseslint.configs.stylisticTypeChecked,
    {
      languageOptions: { parserOptions: { projectService: true, tsconfigRootDir } },
      rules: {
        "@typescript-eslint/consistent-type-imports": "error",
        "@typescript-eslint/no-floating-promises": "error",
        "@typescript-eslint/restrict-template-expressions": ["error", { allowNumber: true, allowBoolean: true }],
        "@typescript-eslint/no-unused-vars": ["error", { argsIgnorePattern: "^_", varsIgnorePattern: "^_" }],
        eqeqeq: ["error", "smart"],
        "no-console": "off",
      },
    },
    {
      files: ["**/*.test.ts", "**/test/**/*.ts"],
      rules: { "@typescript-eslint/no-non-null-assertion": "off", "@typescript-eslint/no-unsafe-assignment": "off" },
    },
    prettier,
  );
}
