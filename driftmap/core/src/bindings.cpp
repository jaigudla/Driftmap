#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "stats.hpp"

namespace py = pybind11;

PYBIND11_MODULE(driftmap_core, m) {
  m.doc() = "Driftmap statistical core";

  m.def("ks_2samp", &driftmap::ks_2samp, py::arg("a"), py::arg("b"));
  m.def("mann_whitney", &driftmap::mann_whitney, py::arg("a"), py::arg("b"));
  m.def("cohen_d", &driftmap::cohen_d, py::arg("a"), py::arg("b"));
}
