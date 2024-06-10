module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
  ],
  ignorePatterns: [
    'dist',
    '.eslintrc.cjs',
    // these are from https://github.com/shadcn-ui/ui, so don't bother linting for now
    'src/components/ui',
  ],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'no-extra-semi': 'off',
    'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
  },
}
