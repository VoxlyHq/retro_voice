import coremltools as ct
import tensorflow as tf

# Load the frozen graph
with tf.io.gfile.GFile('frozen_east_text_detection.pb', 'rb') as f:
    graph_def = tf.compat.v1.GraphDef()
    graph_def.ParseFromString(f.read())

# Import the graph definition into a new graph
with tf.Graph().as_default() as graph:
    tf.import_graph_def(graph_def, name='')

# Define input tensor
input_tensor = graph.get_tensor_by_name('input_images:0')

# Define fixed input shape
fixed_input_shape = (1, 512, 512, 3)

# Convert to Core ML model with image type input
mlmodel = ct.convert(
    'saved_model',
    source='tensorflow',
    inputs=[ct.ImageType(name="input_images", shape=fixed_input_shape, bias=[-1, -1, -1], scale=1/127.5)],
    outputs=['feature_fusion/Conv_7/Sigmoid:0', 'feature_fusion/Conv_8/Sigmoid:0', 'feature_fusion/Conv_9/Sigmoid:0']
)

# Save the Core ML model with .mlpackage extension
mlmodel.save('frozen_east_text_detection.mlpackage')
