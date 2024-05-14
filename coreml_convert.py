import tensorflow as tf

# Load the frozen graph
with tf.io.gfile.GFile('frozen_east_text_detection.pb', 'rb') as f:
    graph_def = tf.compat.v1.GraphDef()
    graph_def.ParseFromString(f.read())

# Import the graph definition into a new graph and save it as a SavedModel
with tf.Graph().as_default() as graph:
    tf.import_graph_def(graph_def, name='')

    # Define a function to save the graph as a SavedModel
    with tf.compat.v1.Session(graph=graph) as sess:
        tf.compat.v1.saved_model.simple_save(
            sess,
            export_dir='saved_model',
            inputs={'input_images': graph.get_tensor_by_name('input_images:0')},
            outputs={
                'feature_fusion/Conv_7/Sigmoid': graph.get_tensor_by_name('feature_fusion/Conv_7/Sigmoid:0'),
                'feature_fusion/concat_3:0': graph.get_tensor_by_name('feature_fusion/concat_3:0'),
            }
        )
