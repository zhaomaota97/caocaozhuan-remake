"""Reproduce observed level-growth arithmetic; attribute names remain provisional."""


def tier(base):
    return 1 if base < 25 else 2 if base < 35 else 3 if base < 45 else 4


def level_up(values, bases, class_growth, level, steps):
    if len(values) != 7 or len(bases) != 5 or len(class_growth) != 7:
        raise ValueError('expected 7 current stats, 5 base stats, 7 class growths')
    if not 1 <= level <= 50 or steps < 0:
        raise ValueError('invalid level or step count')
    steps = min(steps, 50-level)
    increments = [(class_growth[i]+tier(bases[i]))//2 if i < 5 else class_growth[i]
                  for i in range(7)]
    limits = [255]*5+[500,250]
    return [min(limit, value+steps*growth) for value,growth,limit in
            zip(values,increments,limits)], level+steps
