# coding: utf-8


class ExperimentBaseError(BaseException):
    pass


class ExperimentValidateError(ExperimentBaseError):
    pass


class ExperimentGroupNotFindError(ExperimentBaseError):
    pass
