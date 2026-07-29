import FluidAudio
import Foundation

private struct HelperResponse: Encodable {
    let type: String
    let text: String?
    let message: String?

    static func ready() -> HelperResponse {
        HelperResponse(type: "ready", text: nil, message: nil)
    }

    static func result(_ text: String) -> HelperResponse {
        HelperResponse(type: "result", text: text, message: nil)
    }

    static func error(_ message: String) -> HelperResponse {
        HelperResponse(type: "error", text: nil, message: message)
    }
}

@main
private struct VoiceCursorParakeet {
    private static let encoder = JSONEncoder()

    static func main() async {
        do {
            let models = try await AsrModels.downloadAndLoad(version: .v3)
            let manager = AsrManager(config: .default)
            try await manager.loadModels(models)
            emit(.ready())

            while let path = readLine(strippingNewline: true) {
                guard !path.isEmpty else { continue }
                do {
                    let decoderLayers = await manager.decoderLayerCount
                    var state = TdtDecoderState.make(decoderLayers: decoderLayers)
                    let result = try await manager.transcribe(
                        URL(fileURLWithPath: path),
                        decoderState: &state
                    )
                    emit(.result(result.text))
                } catch {
                    emit(.error(error.localizedDescription))
                }
            }
        } catch {
            emit(.error("Parakeet startup failed: \(error.localizedDescription)"))
            Foundation.exit(1)
        }
    }

    private static func emit(_ response: HelperResponse) {
        guard
            let data = try? encoder.encode(response),
            let line = String(data: data, encoding: .utf8)
        else {
            return
        }
        print(line)
        fflush(stdout)
    }
}
