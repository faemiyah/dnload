#ifndef COMMON_HPP
#define COMMON_HPP

#include <cstdint>
#include <iomanip>
#include <sstream>

namespace fcmp
{
  /// Tell if verbose reporting is on?
  ///
  /// \return True if yes, false if no.
  bool is_verbose();

  /// Tell if very verbose reporting is on?
  ///
  /// \return True if yes, false if no.
  bool is_very_verbose();

  /// Set verbose reporting on or off.
  ///
  /// \param level Level of verbosity, 0 to disable.
  void set_verbosity(unsigned level = 0);

  /// Create a mask of given amount of leas significant bits set to 1.
  ///
  /// \param len Number of bits to set.
  /// \return Mask returned.
  inline uint64_t mask_lsb(unsigned len)
  {
    uint64_t ret = static_cast<uint64_t>(1) << (len - 1);
    return (ret - 1) ^ ret;
  }

  /// Convert to bit string.
  ///
  /// \param op Number to convert.
  template <typename T> std::string to_bit_string(const T& op)
  {
    std::ostringstream sstr;
    for(unsigned ii = sizeof(op) * 8; (ii > 0); --ii)
    {
      sstr << static_cast<bool>(op & (static_cast<T>(1) << (ii - 1)));
    }
    return sstr.str();
  }

  /// Convert to hex string.
  ///
  /// \param op Number to convert.
  /// \return Hex representation.
  template <typename T> std::string to_hex_string(const T& op)
  {
    std::ostringstream sstr;
    sstr << std::setfill('0') << std::hex << std::setw(sizeof(op) * 2) << static_cast<size_t>(op);
    return sstr.str();
  }
}

#endif
