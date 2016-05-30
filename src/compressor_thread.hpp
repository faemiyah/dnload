#ifndef COMPRESSOR_THREAD_HPP
#define COMPRESSOR_THREAD_HPP

#include "data_bits.hpp"
#include "threading.hpp"

namespace fcmp
{
  // Forward declaration.
  class CompressorState;

  /// Compressor thread.
  class CompressorThread
  {
    private:
      /// Compression state that owns this thread.
      CompressorState* m_state;

      /// Input data.
      const DataBits *m_data;

      /// Should the thread terminate?
      bool m_terminate;

      /// Condition variable for this thread.
      std::condition_variable m_cond;

      /// Thread.
      std::thread m_thread;

      /// Context.
      uint8_t m_context;

      /// Weight.
      uint8_t m_weight;

      /// Size limit.
      size_t m_size_limit;

    public:
      /// Constructor.
      ///
      /// \param state State that owns this thread.
      /// \param data Input data.
      CompressorThread(CompressorState* state, const DataBits *data);

      /// Destructor.
      ~CompressorThread();

    public:
      /// Accessor.
      ///
      /// \return Condition variable.
      std::condition_variable& getCond()
      {
        return m_cond;
      }
      /// Accessor.
      ///
      /// \return Condition variable.
      const std::condition_variable& getCond() const
      {
        return m_cond;
      }

    public:
      /// Assign a task and wake up this thread.
      ///
      /// \param context Context for next task.
      /// \param weight Weight for next task.
      /// \param size_limit Maximum size to compress up to.
      void awaken(uint8_t context, uint8_t weight, size_t size_limit)
      {
        m_context = context;
        m_weight = weight;
        m_size_limit = size_limit;
        m_cond.notify_one();
      }

    public:
      /// Thread function.
      void run();
  };

  /// Convenience typedef.
  typedef std::shared_ptr<CompressorThread> CompressorThreadSptr;
}

#endif
