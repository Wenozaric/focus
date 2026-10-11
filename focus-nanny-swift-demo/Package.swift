// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "FocusNanny",
    platforms: [.macOS(.v14)],
    products: [
        .executable(name: "FocusNanny", targets: ["FocusNanny"])
    ],
    dependencies: [],
    targets: [
        .executableTarget(
            name: "FocusNanny",
            path: "Sources/FocusNanny"
        )
    ]
)
