# PokeVault iOS

Native iPhone app (SwiftUI) that uses the existing FastAPI backend.

## Setup

1) Install Xcode (Mac required).
2) Install XcodeGen (optional, for generating the project):

```bash
brew install xcodegen
```

3) Generate the Xcode project:

```bash
cd ios
xcodegen
```

4) Open `ios/PokeVault.xcodeproj` in Xcode, set your signing team, and run.

## API Base URL

Edit `ios/PokeVault/Sources/AppConfig.swift` if your API domain changes.

## Offline Image Caching

Images are cached on device using a disk-backed cache in `Library/Caches/images`.
