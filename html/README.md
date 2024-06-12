# WebRTC Frontend (React + TypeScript + Vite)

## Install

```bash
npm install
```

## Development

To launch the frontend in dev mode:
```bash
npm run dev
```

Vite will run the dev server on some random port, it's not currently configured to
auto-launch the browser, so you'll need to open `http://localhost:XXXX/app` manually.

To auto-format the code after making changes:
```bash
npm run format
```

## Production

To build for production:
```bash
npm run build
```

Build artifacts will be written to `../static/app`.

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type aware lint rules:

- Configure the top-level `parserOptions` property like this:

```js
export default {
  // other rules...
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    project: ['./tsconfig.json', './tsconfig.node.json'],
    tsconfigRootDir: __dirname,
  },
}
```

- Replace `plugin:@typescript-eslint/recommended` to `plugin:@typescript-eslint/recommended-type-checked` or `plugin:@typescript-eslint/strict-type-checked`
- Optionally add `plugin:@typescript-eslint/stylistic-type-checked`
