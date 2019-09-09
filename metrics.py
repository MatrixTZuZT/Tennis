"""Precision, Recall and F1 metirc."""
import numpy as np
import mxnet as mx
from mxnet import ndarray
from mxnet.metric import check_label_shapes


class PRF1(mx.metric.EvalMetric):

    def __init__(self, axis=1, name='prf1', output_names=None, label_names=None):
        """
        Computes the per class precision, recall and F1 scores

        Args:
            axis (int): The axis that represents classes (default is 1)
            name (str): Name of this metric instance for display (default is 'prf1')
            output_names (list of str): Name of predictions that should be used when updating with update_dict
            label_names (list of str): Name of labels that should be used when updating with update_dict (required)
        """
        super(PRF1, self).__init__(name, axis=axis, output_names=output_names, label_names=label_names)
        assert label_names is not None, 'label_names cant be None'
        self.axis = axis
        self.label_names = label_names
        self.scores = np.zeros((3, len(label_names)))

    def update(self, labels, preds):
        """
        Update the metric state

        Args:
            labels (list of `NDArray`): The labels of the data with class indices as values, one per sample
            preds (list of `NDArray`): Prediction values for samples. Each prediction value can either be the class
                                       index, or a vector of likelihoods for all classes.

        """

        labels, preds = check_label_shapes(labels, preds, True)

        for label, pred_label in zip(labels, preds):
            if pred_label.shape != label.shape:
                pred_label = ndarray.argmax(pred_label, axis=self.axis)
            pred_label = pred_label.asnumpy().astype('int32')
            label = label.asnumpy().astype('int32')

            labels, preds = check_label_shapes(label, pred_label)

            for i, _ in enumerate(self.label_names):
                predictions = (preds.reshape(-1, 1) == i).all(axis=-1)
                positives = (labels.reshape(-1, 1) == i).all(axis=-1)
                matches = np.logical_and(predictions, positives)

                self.scores[0, i] = matches.sum()
                self.scores[1, i] = positives.sum()
                self.scores[2, i] = predictions.sum()

    def get(self):
        """
        Get the metric values

        Returns:
            scores (list of tuples): of from (str: name, float: value)

        """
        scores = []
        for i, c in enumerate(self.label_names):
            prec = self.scores[0][i] / (self.scores[1][i] + np.finfo(float).eps)
            rec = self.scores[0][i] / (self.scores[2][i] + np.finfo(float).eps)
            f1 = 2 * (prec * rec) / (prec + rec + np.finfo(float).eps)

            scores.append((c+'_prec', prec))
            scores.append((c+'_rec', rec))
            scores.append((c+'_f1', f1))

        return scores

    def reset(self):
        self.scores = np.zeros((3, len(self.label_names)))
