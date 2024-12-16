#include "fps_counter.hpp"

#include <algorithm>
#include <utility>

#include <boost/assert.hpp>

#include <iostream>

namespace
{

/// Gets the read cursor for given storage.
///
/// \param data Storage.
/// \param insert_cursor Insertion cursor.
/// \param num_entries Number of entries.
template<typename T> unsigned get_read_cursor(
        const std::vector<T>& data,
        unsigned insert_cursor,
        unsigned num_entries)
{
    if(insert_cursor < num_entries)
    {
        return static_cast<unsigned>(data.size()) - (num_entries - insert_cursor);
    }
    return insert_cursor - num_entries;
}

/// Creates a larger copy of given vector.
//
/// The data is moved to the beginning.
///
/// \param data Data to read from.
/// \param read_cursor Read cursor.
/// \param num_entries Number of entries.
/// \return Replacement vector.
template <typename T> std::vector<T> resize_storage(
        const std::vector<T>& data,
        unsigned read_cursor,
        unsigned num_entries)
{
    std::vector<T> replacement_data(data.size() * 2);

    for(unsigned ii = read_cursor, jj = 0; (jj < num_entries); ++jj)
    {
        replacement_data[jj] = data[ii];
        ++ii;
        if(ii >= data.size())
        {
            ii = 0;
        }
    }

    return replacement_data;
}

/// Gets the difference between two timestamps.
///
/// Survives from overflow.
///
/// \param first First timestamp.
/// \param second Second timestamp.
/// \return Difference between timestamps.
unsigned timestamp_diff(unsigned first, unsigned second)
{
    if(first > second)
    {
        return static_cast<unsigned>(0xFFFFFFFF) - first + second;
    }
    return second - first;
}

}

std::optional<float> FpsCounter::appendTimestamp(unsigned stamp)
{
    // Increment capacity if the storage is full.
    if(m_num_entries >= m_timestamps.size())
    {
        unsigned read_cursor = get_read_cursor(m_timestamps, m_insert_cursor, m_num_entries);
        m_timestamps = resize_storage(m_timestamps, read_cursor, m_num_entries);
        m_timestamps[m_num_entries] = stamp;
        m_insert_cursor = ++m_num_entries;
    }
    else
    {
        m_timestamps[m_insert_cursor] = stamp;
        if(++m_insert_cursor >= m_timestamps.size())
        {
            m_insert_cursor = 0;
        }
        ++m_num_entries;
    }

    // Decrement number of entries until they're all within the timestamp window.
    unsigned read_cursor = get_read_cursor(m_timestamps, m_insert_cursor, m_num_entries);
    unsigned first_timestamp = m_timestamps[read_cursor];
    unsigned diff = timestamp_diff(first_timestamp, stamp);
    while(diff >= m_window)
    {
        if(++read_cursor >= m_timestamps.size())
        {
            read_cursor = 0;
        }

        --m_num_entries;
        BOOST_ASSERT(m_num_entries);

        first_timestamp = m_timestamps[read_cursor];
        diff = timestamp_diff(first_timestamp, stamp);
    }

    // Do not consider printing unless the current window has exceeded print window.
    BOOST_ASSERT(m_window > m_print_window);
    if(diff > m_print_window)
    {
        // Only return the framerate for printing if both tolerances match.
        float current_fps = static_cast<float>(m_num_entries) / static_cast<float>(diff) * 1000.0f;
        if(std::abs(current_fps - m_last_printed_framerate) >= m_print_tolerance)
        {
            unsigned print_diff = timestamp_diff(m_last_print_timestamp, stamp);
            if(print_diff >= m_print_window)
            {
                m_last_print_timestamp = stamp;
                m_last_printed_framerate = current_fps;
                return current_fps;
            }
        }
    }
    return std::nullopt;
}

