# coding: utf-8


class ExperimentBaseError(Exception):
    pass


class ExperimentValidateError(ExperimentBaseError):
    pass


class ExperimentGroupNotFindError(ExperimentBaseError):
    pass
