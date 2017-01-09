#include "compressor_state.hpp"

#include "common.hpp"
#include "data_compressed.hpp"

#include <iostream>

/// Define to do extra checking during cycles.
#define COMPRESSOR_STATE_EXTRA_CHECKS

using namespace fcmp;

void CompressorState::eraseCompressorThread(CompressorThreadVector &vec, CompressorThread *thr)
{
  for(size_t ii = 0, ee = vec.size(); (ii != ee); ++ii)
  {
    if(vec[ii] == thr)
    {
      vec.erase(vec.begin() + static_cast<ssize_t>(ii));
      return;
    }
  }
}

CompressorState::CompressorState(const DataBits *data, unsigned threads) :
  m_data(data),
  m_compressor(new Compressor())
{
  unsigned ee = threads ? threads : std::thread::hardware_concurrency();

  for(unsigned ii = 0; (ee > ii); ++ii)
  {
    m_threads.push_back(CompressorThreadUptr(new CompressorThread(this, m_data)));
  }
}

void CompressorState::awaken(CompressorThread *thr, uint8_t context, uint8_t weight, size_t size_limit)
{
  eraseCompressorThread(m_threads_dormant, thr);
  m_threads_active.push_back(thr);
  thr->awaken(context, weight, size_limit);
}

bool CompressorState::compressCycle()
{
  ScopedLock sl(m_mutex);

  resetProgress();

  for(unsigned ii = 1; (256 > ii); ++ii)
  {
    uint8_t context = static_cast<uint8_t>(ii);

    for(unsigned jj = 0; (256 > jj); ++jj)
    {
      uint8_t weight = static_cast<uint8_t>((256 <= jj) ? (jj - 256) : jj);

      if(m_threads_dormant.empty())
      {
        m_cond.wait(sl);
      }

      awaken(m_threads_dormant.back(), context, weight,
          m_best_data ? m_best_data->getSizeBits() : std::numeric_limits<size_t>::max());
#if defined(FCMP_COMPRESSION_TRIVIAL)
      break;
#endif
    }
#if defined(FCMP_COMPRESSION_TRIVIAL)
    break;
#endif
  }

  while(m_threads_dormant.size() < m_threads.size())
  {
    m_cond.wait(sl);
  }

  return cycle();
}

bool CompressorState::cycle()
{
  if(!m_next_compressor)
  {
    if(m_compressor->rebase(false) && m_best_data)
    {
      if(is_verbose())
      {
        std::cout << *m_compressor << " (downscale)\n";
      }
      m_best_data->replaceModels(*m_compressor);
    }
    return false;
  }

  m_compressor = m_next_compressor;
  m_next_compressor.reset();

  // Rebase compressor weights to prevent drift.
  if(m_compressor->rebase() && m_best_data)
  {
    if(is_verbose())
    {
      std::cout << *m_compressor << " (rebase)\n";
    }
    m_best_data->replaceModels(*m_compressor);

#if defined(COMPRESSOR_STATE_EXTRA_CHECKS)
    // Check that best data is correct after replacing models.
    DataBitsUptr verify_data = Compressor::extract(*m_best_data);
    if(*verify_data != *m_data)
    {
      std::ostringstream sstr;
      sstr << "rebasing destroyed data:\n" << *verify_data;
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }
#endif
  }

  return true;
}

void CompressorState::update(CompressorSptr compressor, DataCompressedSptr data)
{
  if(!m_best_data || (data->getSizeBits() < m_best_data->getSizeBits()))
  {
    if(is_verbose()) 
    {
      std::cout << *compressor << " -> " << data->getSizeBits() << std::endl;
      printProgress(true);
    }
    m_next_compressor = compressor;
    m_best_data = data;

#if defined(COMPRESSOR_STATE_EXTRA_CHECKS)
    // Check that current best data is correct.
    DataBitsUptr verify_data = Compressor::extract(*m_best_data);
    if(*verify_data != *m_data)
    {
      std::ostringstream sstr;
      sstr << "incorrect compression data created:\n" << *verify_data;
      BOOST_THROW_EXCEPTION(std::runtime_error(sstr.str()));
    }
#endif
  }
  else
  {
    ++m_progress;
    if(is_verbose())
    {
      printProgress();
    }
  }
}

void CompressorState::printProgress(bool force)
{
  // Counter should reach 100% eventually.
  // 65536 / 101 ~= 648.8713
  // 65536 * 648.872 ~= 100.9999
  int progress_print = static_cast<int>(static_cast<float>(m_progress) / 648.872f);

  if(force || (progress_print != m_progress_print))
  {
    m_progress_print = progress_print;
    std::cout << "[ " << std::setw(3) << progress_print << "% ]" << std::flush << "\r        \r";
  }
}

void CompressorState::wait(CompressorThread *thr, ScopedLock &sl)
{
  eraseCompressorThread(m_threads_active, thr);
  waitInitial(thr, sl);
}

void CompressorState::waitInitial(CompressorThread *thr, ScopedLock &sl)
{
  m_threads_dormant.push_back(thr);

  m_cond.notify_one();
  thr->getCond().wait(sl);
}

