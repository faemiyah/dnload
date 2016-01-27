#ifndef THREADING_HPP
#define THREADING_HPP

#include <condition_variable>
#include <mutex>
#include <thread>

namespace fcmp
{
  /// Convenience typedef.
  typedef std::unique_lock<std::mutex> ScopedLock;
}

#endif
