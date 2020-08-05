from numpy import ndarray

class FaceEncoding:
    """
    Represents a facial encoding that is tracked in the database.
    """
    def __init__(self, encoding_id: int, encoding: ndarray):
        self.dbid = encoding_id
        self.encoding = encoding

    def equals(self, other_enc: "FaceEncoding"):
        return (self.encoding == other_enc.encoding).all()
