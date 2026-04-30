#include "stats.hpp"

#include <algorithm>
#include <cmath>
#include <cstddef>
#include <limits>
#include <stdexcept>
#include <vector>

namespace driftmap {

namespace {

void validate_non_empty(const std::vector<double>& a,
                        const std::vector<double>& b) {
  if (a.empty() || b.empty()) {
    throw std::invalid_argument("Input samples must be non-empty");
  }
}

struct Moments {
  double mean = 0.0;
  double sample_variance = 0.0;
};

Moments compute_moments(const std::vector<double>& values) {
  double mean = 0.0;
  double m2 = 0.0;
  std::size_t n = 0;

  for (double value : values) {
    ++n;
    const double delta = value - mean;
    mean += delta / static_cast<double>(n);
    const double delta2 = value - mean;
    m2 += delta * delta2;
  }

  Moments moments;
  moments.mean = mean;
  moments.sample_variance =
      n > 1 ? m2 / static_cast<double>(n - 1) : 0.0;
  return moments;
}

double normal_two_sided_p_value(double z) {
  return std::erfc(std::abs(z) / std::sqrt(2.0));
}

double ks_asymptotic_p_value(double d, std::size_t n1, std::size_t n2) {
  if (d <= 0.0) {
    return 1.0;
  }

  const double n1d = static_cast<double>(n1);
  const double n2d = static_cast<double>(n2);
  const double en = std::sqrt((n1d * n2d) / (n1d + n2d));
  const double lambda = (en + 0.12 + 0.11 / en) * d;

  double p = 0.0;
  for (int k = 1; k <= 100; ++k) {
    const double kk = static_cast<double>(k);
    const double term = std::exp(-2.0 * kk * kk * lambda * lambda);
    if (k % 2 == 1) {
      p += term;
    } else {
      p -= term;
    }
    if (term < 1e-12) {
      break;
    }
  }

  p *= 2.0;
  if (p < 0.0) {
    return 0.0;
  }
  if (p > 1.0) {
    return 1.0;
  }
  return p;
}

}  // namespace

double ks_2samp(const std::vector<double>& a, const std::vector<double>& b) {
  validate_non_empty(a, b);

  std::vector<double> sorted_a = a;
  std::vector<double> sorted_b = b;
  std::sort(sorted_a.begin(), sorted_a.end());
  std::sort(sorted_b.begin(), sorted_b.end());

  const std::size_t n1 = sorted_a.size();
  const std::size_t n2 = sorted_b.size();
  std::size_t i = 0;
  std::size_t j = 0;
  double d = 0.0;

  while (i < n1 && j < n2) {
    const double va = sorted_a[i];
    const double vb = sorted_b[j];
    const double x = (va < vb) ? va : vb;

    while (i < n1 && sorted_a[i] <= x) {
      ++i;
    }
    while (j < n2 && sorted_b[j] <= x) {
      ++j;
    }

    const double cdf_a = static_cast<double>(i) / static_cast<double>(n1);
    const double cdf_b = static_cast<double>(j) / static_cast<double>(n2);
    d = std::max(d, std::abs(cdf_a - cdf_b));
  }

  while (i < n1) {
    ++i;
    const double cdf_a = static_cast<double>(i) / static_cast<double>(n1);
    const double cdf_b = static_cast<double>(j) / static_cast<double>(n2);
    d = std::max(d, std::abs(cdf_a - cdf_b));
  }
  while (j < n2) {
    ++j;
    const double cdf_a = static_cast<double>(i) / static_cast<double>(n1);
    const double cdf_b = static_cast<double>(j) / static_cast<double>(n2);
    d = std::max(d, std::abs(cdf_a - cdf_b));
  }

  return ks_asymptotic_p_value(d, n1, n2);
}

double mann_whitney(const std::vector<double>& a, const std::vector<double>& b) {
  validate_non_empty(a, b);

  const std::size_t n1 = a.size();
  const std::size_t n2 = b.size();
  const std::size_t n = n1 + n2;

  std::vector<std::pair<double, bool>> pooled;
  pooled.reserve(n);
  for (double value : a) {
    pooled.emplace_back(value, true);
  }
  for (double value : b) {
    pooled.emplace_back(value, false);
  }
  std::sort(pooled.begin(), pooled.end(),
            [](const auto& lhs, const auto& rhs) { return lhs.first < rhs.first; });

  double rank_sum_a = 0.0;
  double tie_sum = 0.0;

  std::size_t idx = 0;
  while (idx < n) {
    std::size_t next = idx + 1;
    while (next < n && pooled[next].first == pooled[idx].first) {
      ++next;
    }

    const double t = static_cast<double>(next - idx);
    const double avg_rank =
        (static_cast<double>(idx + 1) + static_cast<double>(next)) / 2.0;
    for (std::size_t k = idx; k < next; ++k) {
      if (pooled[k].second) {
        rank_sum_a += avg_rank;
      }
    }
    tie_sum += t * t * t - t;
    idx = next;
  }

  const double n1d = static_cast<double>(n1);
  const double n2d = static_cast<double>(n2);
  const double nd = static_cast<double>(n);
  const double u1 = rank_sum_a - n1d * (n1d + 1.0) / 2.0;
  const double mean_u = n1d * n2d / 2.0;

  const double tie_correction = tie_sum / (nd * (nd - 1.0));
  const double variance_u =
      n1d * n2d / 12.0 * ((nd + 1.0) - tie_correction);

  if (variance_u <= std::numeric_limits<double>::epsilon()) {
    return std::abs(u1 - mean_u) <= std::numeric_limits<double>::epsilon() ? 1.0
                                                                            : 0.0;
  }

  const double diff = u1 - mean_u;
  const double continuity = (diff > 0.0) ? 0.5 : ((diff < 0.0) ? -0.5 : 0.0);
  const double z = (diff - continuity) / std::sqrt(variance_u);
  return normal_two_sided_p_value(z);
}

double cohen_d(const std::vector<double>& a, const std::vector<double>& b) {
  validate_non_empty(a, b);

  const Moments a_moments = compute_moments(a);
  const Moments b_moments = compute_moments(b);
  const double n1 = static_cast<double>(a.size());
  const double n2 = static_cast<double>(b.size());
  const double mean_diff = a_moments.mean - b_moments.mean;

  const double dof = n1 + n2 - 2.0;
  const double pooled_var =
      dof > 0.0 ? (((n1 - 1.0) * a_moments.sample_variance) +
                   ((n2 - 1.0) * b_moments.sample_variance)) /
                      dof
                : 0.0;
  const double pooled_std = pooled_var > 0.0 ? std::sqrt(pooled_var) : 0.0;

  if (pooled_std <= std::numeric_limits<double>::epsilon()) {
    if (std::abs(mean_diff) <= std::numeric_limits<double>::epsilon()) {
      return 0.0;
    }
    throw std::invalid_argument(
        "Cohen's d is undefined when pooled standard deviation is zero");
  }

  return mean_diff / pooled_std;
}

}  // namespace driftmap
