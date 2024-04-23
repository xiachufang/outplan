class GroupResultType:
    """Type of group item result"""

    group = 1  # return result directly
    layer = 2  # namespace nested


class UserTagFilterType:
    AND = 1
    OR = 2


ONE_MINUTE = 60
ONE_HOUR = ONE_MINUTE * 60
