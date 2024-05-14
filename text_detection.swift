import Foundation
import CoreML
import Vision
import Cocoa

// Function to measure the execution time of a closure
func measure<T>(_ block: () -> T) -> (result: T, duration: TimeInterval) {
    let start = Date()
    let result = block()
    let end = Date()
    return (result, end.timeIntervalSince(start))
}

// Function to detect text in an image
func detectText(in image: CGImage, model: VNCoreMLModel) -> (duration: TimeInterval, results: [VNCoreMLFeatureValueObservation])? {
    let request = VNCoreMLRequest(model: model) { (request, error) in
        // This will be populated with results in completion handler
    }

    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    let result = measure {
        try? handler.perform([request])
    }

    guard let observations = request.results as? [VNCoreMLFeatureValueObservation] else {
        return nil
    }

    return (result.duration, observations)
}

// Load the Core ML model
guard let modelURL = URL(string: "file://" + FileManager.default.currentDirectoryPath + "/frozen_east_text_detection.mlpackage") else {
    fatalError("Failed to load model")
}

guard let compiledModelURL = try? MLModel.compileModel(at: modelURL) else {
    fatalError("Failed to compile model")
}

let model = try VNCoreMLModel(for: MLModel(contentsOf: compiledModelURL))

// Load the image
let imagePath = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fatalError("Failed to load image")
}

// Run the text detection 100 times and calculate the average duration
var totalDuration: TimeInterval = 0
let runCount = 100

for _ in 0..<runCount {
    if let result = detectText(in: cgImage, model: model) {
        totalDuration += result.duration
    } else {
        fatalError("Text detection failed")
    }
}

let averageDuration = totalDuration / Double(runCount)
print("Average duration for text detection: \(averageDuration) seconds")
