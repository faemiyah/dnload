#include "compressor_thread.hpp"

#include "compressor_state.hpp"

using namespace fcmp;

CompressorThread::CompressorThread(CompressorState *state, const DataBits *data) :
  m_state(state),
  m_data(data),
  m_terminate(false)
{
  m_thread = std::thread(std::bind(&CompressorThread::run, this));
}

CompressorThread::~CompressorThread()
{
  m_terminate = true;
  m_cond.notify_one();
  m_thread.join();
}

void CompressorThread::run()
{
  ScopedLock sl(m_state->getMutex());

  m_state->waitInitial(this, sl);

  while(!m_terminate)
  {
    sl.unlock();

    // It is guaranteed that mutating compressor will not change in-between.
    CompressorSptr compressor = m_state->mutate(m_context, m_weight);
    if(compressor)
    {
      DataCompressedSptr attempt = compressor->compressRun(*m_data, m_size_limit);
      sl.lock();
      m_state->update(compressor, attempt);
    }
    else
    {
      sl.lock();
    }

    m_state->wait(this, sl);
  }
}

