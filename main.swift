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

func decodePredictions(scores: MLMultiArray, geometry: MLMultiArray, rW: Double, rH: Double) -> (rects: [(CGRect)], confidences: [Double]) {
    var rects: [(CGRect)] = []
    var confidences: [Double] = []
    
    let numRows = scores.shape[2].intValue
    let numCols = scores.shape[3].intValue

    for y in 0..<numRows {
        // Extract scores and geometry data for this row
        let scoresData = scoresPointer(scores: scores, row: y)
        let xData0 = geometryPointer(geometry: geometry, row: y, channel: 0)
        let xData1 = geometryPointer(geometry: geometry, row: y, channel: 1)
        let xData2 = geometryPointer(geometry: geometry, row: y, channel: 2)
        let xData3 = geometryPointer(geometry: geometry, row: y, channel: 3)
        let anglesData = geometryPointer(geometry: geometry, row: y, channel: 4)

        for x in 0..<numCols {
            let score = scoresData[x]

            // Ignore low confidence scores
            if score < 0.1 { // Adjusted threshold
                continue
            }

            // Calculate the offset
            let offsetX = Double(x) * 4.0
            let offsetY = Double(y) * 4.0

            // Extract angle and calculate cos and sin
            let angle = anglesData[x]
            let cos = cos(angle)
            let sin = sin(angle)

            // Calculate width and height
            let h = xData0[x] + xData2[x]
            let w = xData1[x] + xData3[x]

            // Calculate bounding box coordinates
            let endX = offsetX + (cos * xData1[x]) + (sin * xData2[x])
            let endY = offsetY - (sin * xData1[x]) + (cos * xData2[x])
            let startX = endX - w
            let startY = endY - h

            // Adjust the bounding box coordinates based on the original image size
            let adjustedRect = CGRect(
                x: startX * rW,
                y: startY * rH,
                width: w * rW,
                height: h * rH
            )

            rects.append(adjustedRect)
            confidences.append(score)
        }
    }
    
    return (rects, confidences)
}

func scoresPointer(scores: MLMultiArray, row: Int) -> [Double] {
    let shape = scores.shape
    let pointer = UnsafeMutablePointer<Double>(OpaquePointer(scores.dataPointer))
    let stride = shape[2].intValue * shape[3].intValue
    let start = stride * row
    let end = start + shape[3].intValue
    return Array(UnsafeBufferPointer(start: pointer + start, count: end - start))
}

func geometryPointer(geometry: MLMultiArray, row: Int, channel: Int) -> [Double] {
    let shape = geometry.shape
    let pointer = UnsafeMutablePointer<Double>(OpaquePointer(geometry.dataPointer))
    let stride = shape[1].intValue * shape[2].intValue * shape[3].intValue
    let channelStride = shape[2].intValue * shape[3].intValue
    let start = stride * 0 + channelStride * channel + shape[3].intValue * row
    let end = start + shape[3].intValue
    return Array(UnsafeBufferPointer(start: pointer + start, count: end - start))
}

func drawRectangles(on image: CGImage, rects: [CGRect]) -> NSImage? {
    let nsImage = NSImage(cgImage: image, size: NSSize(width: image.width, height: image.height))
    let outputImage = NSImage(size: nsImage.size)
    
    outputImage.lockFocus()
    nsImage.draw(at: .zero, from: NSRect(origin: .zero, size: nsImage.size), operation: .sourceOver, fraction: 1.0)
    
    let path = NSBezierPath()
    for rect in rects {
        path.appendRect(rect)
    }
    
    NSColor.red.set()
    path.lineWidth = 2
    path.stroke()
    
    outputImage.unlockFocus()
    
    return outputImage
}

func main() {
    // Load the Core ML model
    guard let modelURL = URL(string: "file://" + "/Users/hyper/projects/me/retro_voiceover" + "/frozen_east_text_detection.mlpackage") else {
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
    let runCount = 120
    
    var finalRects: [CGRect] = []
    
    for i in 0..<runCount {
        if let result = detectText(in: resizedCGImage, model: model) {
            totalDuration += result.duration
            print("Run \(i + 1): Duration: \(result.duration) seconds")
            
            guard result.results.count >= 2,
                  let scores = result.results[0].featureValue.multiArrayValue,
                  let geometry = result.results[1].featureValue.multiArrayValue else {
                print("Invalid results for run \(i + 1)")
                continue
            }
            
            let (rects, confidences) = decodePredictions(scores: scores, geometry: geometry, rW: rW, rH: rH)
            if !rects.isEmpty {
                finalRects.append(contentsOf: rects)
            }
            
            print("Detected text for run \(i + 1):")
            for rect in rects {
                print("Text detected at \(rect)")
            }
        } else {
            print("Text detection failed on run \(i + 1)")
        }
    }
    
    // Draw rectangles on the image
    if !finalRects.isEmpty {
        if let annotatedImage = drawRectangles(on: cgImage, rects: finalRects) {
            // Save the annotated image to disk
            let outputPath = "/Users/hyper/Desktop/annotated_image.png"
            let imageData = annotatedImage.tiffRepresentation
            let bitmapImageRep = NSBitmapImageRep(data: imageData!)
            let pngData = bitmapImageRep?.representation(using: .png, properties: [:])
            try? pngData?.write(to: URL(fileURLWithPath: outputPath))
            print("Annotated image saved to \(outputPath)")
        }
    } else {
        print("No text detected in any run.")
    }
    
    let averageDuration = totalDuration / Double(runCount)
    print("Average duration for text detection: \(averageDuration) seconds")
    print("Total duration for text detection: \(totalDuration) seconds")
}

main()
