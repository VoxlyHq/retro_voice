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

    printMultiArrayDetails(scoreArray)
    
    let geometryShape = geometryArray.shape
    let scoreShape = scoreArray.shape

    print("Geometry Shape: \(geometryShape)")
    print("Score Array Shape: \(scoreShape)")

    let geometryCount = geometryArray.count
    let scoreCount = scoreArray.count

    // Lowered threshold for text detection
    for y in 0..<80 {
        for x in 0..<80 {
            let index = (0 * 80 * 80) + (y * 80) + x
            let key = [0,y,x] as [NSNumber]
            let score = scoreArray[key].doubleValue
                let baseIndex = index * 4
                let offsetX = geometryArray[baseIndex].doubleValue
                let offsetY = geometryArray[baseIndex + 1].doubleValue
                let width = geometryArray[baseIndex + 2].doubleValue
                let height = geometryArray[baseIndex + 3].doubleValue


            if score > 0.1 { // Lowered threshold for considering a valid text box

                let coordinates = [
                    CGPoint(x:offsetX, y: offsetY),
                    CGPoint(x:offsetX + width, y: Double(y) * 4.0 + offsetY),
                    CGPoint(x: Double(x) * 4.0 + offsetX + width, y: Double(y) * 4.0 + offsetY + height),
                    CGPoint(x: Double(x) * 4.0 + offsetX, y: Double(y) * 4.0 + offsetY + height)
                ]

                detectedTexts.append(("Text Detected", coordinates))
                print("Detected text with score \(score) at \(coordinates)")
            }
        }
    }

    return detectedTexts
}

// Function to draw detected text annotations on an image
func drawAnnotations(on image: NSImage, with detections: [(text: String, coordinates: [CGPoint])]) -> NSImage? {
    let size = image.size
    let newImage = NSImage(size: size)
    newImage.lockFocus()

    let context = NSGraphicsContext.current?.cgContext
    context?.draw(image.cgImage(forProposedRect: nil, context: nil, hints: nil)!, in: CGRect(origin: .zero, size: size))

    context?.setLineWidth(2.0)
    context?.setStrokeColor(NSColor.red.cgColor)

    for detection in detections {
        let path = CGMutablePath()
        let coords = detection.coordinates
        path.move(to: coords[0])
        path.addLine(to: coords[1])
        path.addLine(to: coords[2])
        path.addLine(to: coords[3])
        path.closeSubpath()

        context?.addPath(path)
        context?.strokePath()
    }

    newImage.unlockFocus()
    return newImage
}


func printMultiArrayDetails(_ multiArray: MLMultiArray) {
    let shape = multiArray.shape
    let count = shape.count

    print("MultiArray Dimensions: \(count)")

    // Print the size of each dimension
    for i in 0..<count {
        print("Dimension \(i + 1): \(shape[i])")
    }

    // Print all values in the multi-array
    var indices = [Int](repeating: 0, count: count)
    printValues(of: multiArray, shape: shape, indices: &indices, dimension: 0)
}

private func printValues(of multiArray: MLMultiArray, shape: [NSNumber], indices: inout [Int], dimension: Int) {
    if dimension == shape.count {
        let indexArray = indices.map { NSNumber(value: $0) }
        let value = multiArray[indexArray]
        print("Value at \(indices): \(value)")
        return
    }

    for i in 0..<shape[dimension].intValue {
        indices[dimension] = i
        printValues(of: multiArray, shape: shape, indices: &indices, dimension: dimension + 1)
    }
}


func main() {
    // Load the Core ML model
    guard let modelURL = URL(string: "file:///Users/hyper/projects/me/retro_voiceover/frozen_east_text_detection.mlpackage") else {
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

    
    //Load the image
    let imagePath = "/Users/hyper/Desktop/ff2_en_1.png"
     guard let image = NSImage(contentsOfFile: imagePath),
              let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
            fatalError("Failed to load image")
       }
    
       // Get original image dimensions
        let origW = cgImage.width
        let origH = cgImage.height
    
        // Set the new width and height (nearest multiple of 32)
        let newW = 320
        let newH = 320
        let rW = Double(origW) / Double(newW)
        let rH = Double(origH) / Double(newH)
    
        // Resize the image
    let resizedImage = NSImage(size: NSSize(width: newW, height: newH))
        resizedImage.lockFocus()
        image.draw(in: NSRect(x: 0, y: 0, width: newW, height: newH))
        resizedImage.unlockFocus()
        guard let resizedCGImage = resizedImage.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
            fatalError("Failed to resize image")
        }
    
        // Run the text detection 100 times and calculate the average duration
    var totalDuration: TimeInterval = 0
    let runCount = 2
    
    var finalRects: [CGRect] = []
    
        
    for i in 0..<runCount {
        if let result = detectText(in: resizedCGImage, model: model) {
            totalDuration += result.duration
            print("Run \(i + 1): Duration: \(result.duration) seconds")

            let detectedTexts = extractTextAndCoordinates(from: result.results)
            print("Detected text for run \(i + 1):")
            for (text, coordinates) in detectedTexts {
                print("\(text) at \(coordinates)")
            }

            // Annotate and save the image
            if let annotatedImage = drawAnnotations(on: image, with: detectedTexts) {
                let outputPath = "annotated_image_\(i + 1).png"
                let outputUrl = URL(fileURLWithPath: outputPath)
                if let tiffData = annotatedImage.tiffRepresentation,
                   let bitmapImage = NSBitmapImageRep(data: tiffData),
                   let pngData = bitmapImage.representation(using: .png, properties: [:]) {
                    do {
                        try pngData.write(to: outputUrl)
                        print("Saved annotated image to \(outputPath)")
                    } catch {
                        print("Failed to save annotated image: \(error)")
                    }
                }
            }
        } else {
            print("Text detection failed on run \(i + 1)")
        }
    }

    let averageDuration = totalDuration / Double(runCount)
    print("Average duration for text detection: \(averageDuration) seconds")
    print("Total duration for text detection: \(totalDuration) seconds")
}

main()
