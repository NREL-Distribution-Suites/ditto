from typing import Annotated

from gdm.constants import PINT_SCHEMA
from infrasys import Component
import opendssdirect as odd
from pydantic import Field
import numpy as np


class AdmittanceMatrix(Component):
    y_bus_real: Annotated[
        list[float],
        PINT_SCHEMA,
        Field(..., description="CSC format data array of the matrix (real)"),
    ]
    y_bus_imag: Annotated[
        list[float],
        PINT_SCHEMA,
        Field(..., description="CSC format data array of the matrix (imag)"),
    ]
    indices: Annotated[
        list[int],
        PINT_SCHEMA,
        Field(..., description="CSC format index array of the matrix"),
    ]
    indptr: Annotated[
        list[int],
        PINT_SCHEMA,
        Field(..., description="CSC format index pointer array of the matrix"),
    ]
    node_list: Annotated[
        list[str],
        PINT_SCHEMA,
        Field(..., description="Node list."),
    ]


def get_admittance_matrix():
    data, indices, indptrs = odd.YMatrix.getYsparse()
    admittance_matrix = AdmittanceMatrix(
        name="admittance_matrix",
        y_bus_real=list(np.real(data)),
        y_bus_imag=list(np.imag(data)),
        indices=list(indices),
        indptr=list(indptrs),
        node_list=odd.Circuit.YNodeOrder(),
    )
    return admittance_matrix
