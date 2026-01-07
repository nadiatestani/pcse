import numpy as np

def afgen2cols(tbl_xyz, x, col_id):
    xs = []
    y1s = []
    y2s = []
    for i in range(len(tbl_xyz)):
        if i % 3 == 0:
            xs.append(tbl_xyz[i])
        elif (i - 1) % 3 == 0:
            y1s.append(tbl_xyz[i])
        else:
            y2s.append(tbl_xyz[i])
    if (col_id == 0):
        raise Exception("The first column contains control variables and cannot be the column id")
    elif (col_id == 1):
        ys = y1s
    elif (col_id == 2):
        ys = y2s
    else:
        raise Exception("The function afgen2cols only supports table functions with two columns")
    # linear_interpolation_function = interpolate.interp1d(xs, ys)
    y = np.interp(x, xs, ys)
    return y