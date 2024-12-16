#ifndef FPS_COUNTER_HPP
#define FPS_COUNTER_HPP

#include <optional>
#include <vector>

/// FPS counter class.
class FpsCounter
{
private:
    /// Frame counting window (milliseconds).
    unsigned m_window = 8000;

    /// Frame printing window (milliseconds).
    unsigned m_print_window = 5000;

    /// Framerate printing tolerance (frames per second).
    float m_print_tolerance = 1.0f;

    /// Last print timestamp.
    unsigned m_last_print_timestamp = 0;

    /// Last printed framerate.
    float m_last_printed_framerate = 0.0f;

    /// Insertion cursor.
    unsigned m_insert_cursor = 0;

    /// Number of entries contained.
    unsigned m_num_entries = 0;

    /// Container for frame timestamps.
    ///
    /// Treated as a circular buffer.
    std::vector<unsigned> m_timestamps;

public:
    /// Default constructor.
    explicit FpsCounter() :
        m_timestamps(128)
    {
    }

    /// Initializing constructor.
    ///
    /// \param window Frame timestamps window.
    /// \param print_window Frame printing window.
    /// \param print_tolerance Frame printing tolerance.
    explicit FpsCounter(unsigned window, unsigned print_window, float print_tolerance) :
        m_window(window),
        m_print_window(print_window),
        m_print_tolerance(print_tolerance),
        m_timestamps(128)
    {
    }

public:
    /// Append a frame.
    ///
    /// \param stamp Timestamp to append.
    /// \return Optional framerate to print.
    std::optional<float> appendTimestamp(unsigned stamp);
};

#endif
