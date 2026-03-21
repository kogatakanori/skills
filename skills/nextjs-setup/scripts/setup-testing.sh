#!/bin/bash
set -e

# テスト環境のセットアップスクリプト

echo "🧪 テスト環境をセットアップ中..."

# Jest & React Testing Library
echo "📦 Jest & React Testing Libraryをインストール中..."
npm install --save-dev jest jest-environment-jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event

# TypeScriptサポート
if [ -f "tsconfig.json" ]; then
    echo "📦 TypeScript用のテストパッケージをインストール中..."
    npm install --save-dev @types/jest ts-jest
fi

# Cypress (E2Eテスト)
read -p "CypressをインストールしますかTUIフレームワーク？（E2Eテスト用） (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install --save-dev cypress
    npx cypress install
fi

# Playwright (E2Eテスト - 代替)
read -p "Playwrightをインストールしますか？（E2Eテスト用、Cypressの代替） (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    npm install --save-dev @playwright/test
    npx playwright install
fi

# jest.config.jsの作成
cat > jest.config.js << 'EOF'
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
  dir: './',
})

// Add any custom config to be passed to Jest
const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  coverageDirectory: 'coverage',
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/_*.{js,jsx,ts,tsx}',
  ],
}

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
module.exports = createJestConfig(customJestConfig)
EOF

# jest.setup.jsの作成
cat > jest.setup.js << 'EOF'
import '@testing-library/jest-dom'
EOF

echo "✅ テスト環境のセットアップが完了しました"
echo ""
echo "NPMスクリプトに以下を追加してください:"
echo '  "test": "jest --watch"'
echo '  "test:ci": "jest --ci"'
echo '  "test:coverage": "jest --coverage"'