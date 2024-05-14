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
        if let error = error {
            print("Error during VNCoreMLRequest: \(error)")
        }
    }

    let handler = VNImageRequestHandler(cgImage: image, options: [:])
    let result = measure {
        do {
            try handler.perform([request])
        } catch {
            print("Error during handler.perform: \(error)")
        }
    }

    guard let observations = request.results as? [VNCoreMLFeatureValueObservation] else {
        print("Failed to cast results to VNCoreMLFeatureValueObservation")
        return nil
    }

    return (result.duration, observations)
}

// Function to extract text from feature values
func extractText(from observations: [VNCoreMLFeatureValueObservation]) -> [String] {
    var detectedTexts: [String] = []

    for observation in observations {
        guard let multiArray = observation.featureValue.multiArrayValue else {
            continue
        }

        // Process the multiArray to extract text data
        // This is a placeholder, actual implementation will depend on the model's output format
        // Here, we just print the shape and some values as an example
        let shape = multiArray.shape
        print("Detected feature with shape: \(shape)")

        // Assuming multiArray contains the text detection scores or coordinates
        let count = multiArray.count
        let step = max(1, count / 10)  // Print up to 10 values to avoid excessive output
        for i in stride(from: 0, to: count, by: step) {
            let value = multiArray[i].doubleValue
            detectedTexts.append("\(value)")
        }
    }

    return detectedTexts
}

// Load the Core ML model
guard let modelURL = URL(string: "file://" + FileManager.default.currentDirectoryPath + "/frozen_east_text_detection.mlpackage") else {
    fatalError("Failed to load model URL")
}

guard let compiledModelURL = try? MLModel.compileModel(at: modelURL) else {
    fatalError("Failed to compile model")
}

let model: VNCoreMLModel
do {
    model = try VNCoreMLModel(for: MLModel(contentsOf: compiledModelURL))
} catch {
    fatalError("Failed to create VNCoreMLModel: \(error)")
}

// Load the image
let imagePath = CommandLine.arguments[1]
guard let image = NSImage(contentsOfFile: imagePath),
      let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
    fatalError("Failed to load image")
}

// Run the text detection 100 times and calculate the average duration
var totalDuration: TimeInterval = 0
let runCount = 100

for i in 0..<runCount {
    if let result = detectText(in: cgImage, model: model) {
        totalDuration += result.duration
        print("Run \(i + 1): Duration: \(result.duration) seconds")
        
        let detectedTexts = extractText(from: result.results)
        for text in detectedTexts {
            print("Detected text: \(text)")
        }
    } else {
        print("Text detection failed on run \(i + 1)")
    }
}

let averageDuration = totalDuration / Double(runCount)
print("Average duration for text detection: \(averageDuration) seconds")
