#include <vector>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "stats.hpp"

namespace py = pybind11;

namespace {

std::vector<double> to_double_vector(py::handle obj) {
  if (py::isinstance<py::str>(obj) || py::isinstance<py::bytes>(obj)) {
    throw py::type_error(
        "arguments must be sequences of floats, not str or bytes");
  }

  std::vector<double> out;
  py::iterator it = py::iter(obj);
  py::iterator end;
  while (it != end) {
    out.push_back(py::cast<double>(*it));
    ++it;
  }
  return out;
}

template <double (*Fn)(const std::vector<double>&, const std::vector<double>&)>
double wrap(py::object a, py::object b) {
  try {
    return Fn(to_double_vector(a), to_double_vector(b));
  } catch (const std::invalid_argument& e) {
    throw py::value_error(e.what());
  }
}

}  // namespace

PYBIND11_MODULE(driftmap_core, m) {
  m.doc() = "Driftmap statistical core";

  m.def("ks_2samp", &wrap<driftmap::ks_2samp>, py::arg("a"), py::arg("b"));
  m.def("mann_whitney", &wrap<driftmap::mann_whitney>, py::arg("a"), py::arg("b"));
  m.def("cohen_d", &wrap<driftmap::cohen_d>, py::arg("a"), py::arg("b"));
}
