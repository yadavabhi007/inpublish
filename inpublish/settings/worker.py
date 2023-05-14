from inpublish.settings import Docker


class Worker(Docker):
    DATA_UPLOAD_MAX_MEMORY_SIZE = 1073741824
    FILE_UPLOAD_MAX_MEMORY_SIZE = 1073741824
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 5000
