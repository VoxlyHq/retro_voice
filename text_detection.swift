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

// Function to extract text and coordinates from feature values
func extractTextAndCoordinates(from observations: [VNCoreMLFeatureValueObservation]) -> [(text: String, coordinates: [CGPoint])] {
    var detectedTexts: [(text: String, coordinates: [CGPoint])] = []

    // Assuming the second observation is the geometry map
    guard observations.count >= 2, let geometryArray = observations[1].featureValue.multiArrayValue else {
        return detectedTexts
    }

    // Assuming the first observation is the score map
    guard let scoreArray = observations[0].featureValue.multiArrayValue else {
        return detectedTexts
    }

    let geometryShape = geometryArray.shape
    let scoreShape = scoreArray.shape

    print("Geometry Shape: \(geometryShape)")
    print("Score Array Shape: \(scoreShape)")

    let geometryCount = geometryArray.count
    let scoreCount = scoreArray.count

    // Debugging: print score map values for the first 10x10 region
    print("Score map values (first 10x10 region):")
    for y in 0..<10 {
        for x in 0..<10 {
            let index = (0 * 128 * 128) + (y * 128) + x
            print(scoreArray[index].doubleValue, terminator: " ")
        }
        print()
    }

    // Debugging: print geometry map values for the first 10x10 region
    print("Geometry map values (first 10x10 region):")
    for y in 0..<10 {
        for x in 0..<10 {
            let baseIndex = ((0 * 128 * 128) + (y * 128) + x) * 4
            let offsetX = geometryArray[baseIndex].doubleValue
            let offsetY = geometryArray[baseIndex + 1].doubleValue
            let width = geometryArray[baseIndex + 2].doubleValue
            let height = geometryArray[baseIndex + 3].doubleValue

            print("(\(offsetX), \(offsetY), \(width), \(height))", terminator: " ")
        }
        print()
    }

    // Lowered threshold for text detection
    for y in 0..<128 {
        for x in 0..<128 {
            let index = (0 * 128 * 128) + (y * 128) + x
            let score = scoreArray[index].doubleValue

            if score > 0.1 { // Lowered threshold for considering a valid text box
                let baseIndex = index * 4
                let offsetX = geometryArray[baseIndex].doubleValue
                let offsetY = geometryArray[baseIndex + 1].doubleValue
                let width = geometryArray[baseIndex + 2].doubleValue
                let height = geometryArray[baseIndex + 3].doubleValue

                let coordinates = [
                    CGPoint(x: Double(x) * 128.0 + offsetX, y: Double(y) * 128.0 + offsetY),
                    CGPoint(x: Double(x) * 128.0 + offsetX + width, y: Double(y) * 128.0 + offsetY),
                    CGPoint(x: Double(x) * 128.0 + offsetX + width, y: Double(y) * 128.0 + offsetY + height),
                    CGPoint(x: Double(x) * 128.0 + offsetX, y: Double(y) * 128.0 + offsetY + height)
                ]

                detectedTexts.append(("Text Detected", coordinates))
                print("Detected text with score \(score) at \(coordinates)")
            }
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
        
        let detectedTexts = extractTextAndCoordinates(from: result.results)
        print("Detected text for run \(i + 1):")
        for (text, coordinates) in detectedTexts {
            print("\(text) at \(coordinates)")
        }
    } else {
        print("Text detection failed on run \(i + 1)")
    }
}

let averageDuration = totalDuration / Double(runCount)
print("Average duration for text detection: \(averageDuration) seconds")
