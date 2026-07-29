// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "VoiceCursorParakeet",
    platforms: [.macOS(.v14)],
    dependencies: [
        .package(
            url: "https://github.com/FluidInference/FluidAudio",
            exact: "0.15.4"
        )
    ],
    targets: [
        .executableTarget(
            name: "voice-cursor-parakeet",
            dependencies: [
                .product(name: "FluidAudio", package: "FluidAudio")
            ]
        )
    ]
)
