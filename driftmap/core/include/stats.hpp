#pragma once

#include <vector>

namespace driftmap {

double ks_2samp(const std::vector<double>& a, const std::vector<double>& b);
double mann_whitney(const std::vector<double>& a, const std::vector<double>& b);
double cohen_d(const std::vector<double>& a, const std::vector<double>& b);

}  // namespace driftmap
