from pyspark.ml.regression import LinearRegressionModel
from pyspark.ml.tuning import TrainValidationSplitModel


class CustomModel:

    model = LinearRegressionModel()

    def __init__(self, pmodel):
        self.model = pmodel
        #self.model = LinearRegressionModel(pmodel)
        model = pmodel

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        del state['model']
        return state
        #return self.__dict__

    def __setstate__(self, state):
        # Restore instance attributes (i.e., filename and lineno).
        self.__dict__.update(state)

    def getModel(self):
        return self.model
