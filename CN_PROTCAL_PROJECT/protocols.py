
import heapq
import random


def simulate_protocol(
    protocol,
    window_size,
    num_frames,
    transmission_delay,
    ack_delay,
    packet_loss,
    ack_loss,
    timeout
):
    # ---------------- VALIDATION ----------------

    valid_protocols = [
        "One-Bit Sliding Window",
        "Go-Back-N",
        "Selective Repeat"
    ]

    if protocol not in valid_protocols:
        raise ValueError("Invalid protocol selected.")

    if (
        not isinstance(window_size, int)
        or not isinstance(num_frames, int)
        or window_size < 1
        or num_frames < 1
    ):
        raise ValueError("Window size and frame count must be positive integers.")

    if protocol == "One-Bit Sliding Window":
        window_size = 1

    if protocol == "Selective Repeat":
        # Standard SR requires a window no larger than half
        # the sequence-number space. This simulator uses
        # absolute frame indexes internally, so we retain
        # the configured window for this simplified model.
        window_size = max(1, window_size)

    if transmission_delay <= 0 or ack_delay < 0 or timeout <= 0:
        raise ValueError("Invalid delay or timeout.")

    if not 0 <= packet_loss <= 100:
        raise ValueError("Packet loss must be between 0 and 100.")

    if not 0 <= ack_loss <= 100:
        raise ValueError("ACK loss must be between 0 and 100.")

    is_one_bit = protocol == "One-Bit Sliding Window"
    is_gbn = protocol == "Go-Back-N"
    is_sr = protocol == "Selective Repeat"

    # ---------------- STATE ----------------

    events = []
    event_id = 0
    current_time = 0

    base = 0
    next_frame = 0
    receiver_expected = 0

    acknowledged = set()
    received_frames = set()

    attempts = [0] * num_frames
    timer_generation = [0] * num_frames
    timer_running = [False] * num_frames

    max_attempts = 50

    stats = {
        "total_frames_transmitted": 0,
        "retransmissions": 0,
        "packets_lost": 0,
        "acks_received": 0
    }

    event_log = []

    # ---------------- HELPER FUNCTIONS ----------------

    def sequence_number(frame):
        # Alternating bit: 0, 1, 0, 1, ...
        return frame % 2

    def record(kind, frame, message):
        event_log.append({
            "type": kind,
            "frame": frame,
            "message": message,
            "time": current_time
        })

    def schedule(time, kind, frame, generation=0):
        nonlocal event_id

        event_id += 1

        heapq.heappush(
            events,
            (time, event_id, kind, frame, generation)
        )

    # ---------------- TIMER MANAGEMENT ----------------

    def start_timer(frame):
        if not 0 <= frame < num_frames:
            return

        timer_generation[frame] += 1
        timer_running[frame] = True

        schedule(
            current_time + timeout,
            "timeout",
            frame,
            timer_generation[frame]
        )

    def invalidate_timer(frame):
        if 0 <= frame < num_frames:
            timer_generation[frame] += 1
            timer_running[frame] = False

    # ---------------- TRANSMISSION ----------------

    def send_frame(frame):
        if attempts[frame] >= max_attempts:
            record(
                "limit",
                frame,
                f"Frame {frame} reached retry limit"
            )
            return False

        attempts[frame] += 1
        stats["total_frames_transmitted"] += 1

        seq = sequence_number(frame)

        if attempts[frame] == 1:
            message = (
                f"Frame {frame} sent with sequence {seq}"
                if is_one_bit
                else f"Frame {frame} sent"
            )
            record("send", frame, message)
        else:
            stats["retransmissions"] += 1

            message = (
                f"Frame {frame} retransmitted with sequence {seq}"
                if is_one_bit
                else f"Frame {frame} retransmitted"
            )
            record("retransmit", frame, message)

        # Simulate data packet loss.
        if random.random() * 100 < packet_loss:
            stats["packets_lost"] += 1
            record("lost", frame, f"Frame {frame} lost")
        else:
            schedule(
                current_time + transmission_delay,
                "packet",
                frame
            )

        # One-Bit and SR use per-frame timers.
        if is_one_bit or is_sr:
            start_timer(frame)

        return True

    # ---------------- WINDOW MANAGEMENT ----------------

    def fill_window():
        nonlocal next_frame

        while (
            next_frame < num_frames
            and next_frame < base + window_size
        ):
            frame = next_frame
            next_frame += 1
            send_frame(frame)

        # Go-Back-N uses one timer for the oldest outstanding frame.
        if (
            is_gbn
            and base < next_frame
            and base < num_frames
            and attempts[base] < max_attempts
            and not timer_running[base]
        ):
            start_timer(base)

    # ---------------- INITIAL TRANSMISSION ----------------

    fill_window()

    # ---------------- EVENT LOOP ----------------

    while events and len(acknowledged) < num_frames:

        current_time, _, kind, frame, generation = heapq.heappop(events)

        # ==================================================
        # PACKET ARRIVAL
        # ==================================================

        if kind == "packet":

            if is_one_bit:
                seq = sequence_number(frame)

                if frame == receiver_expected:
                    received_frames.add(frame)
                    receiver_expected += 1

                    record(
                        "receive",
                        frame,
                        f"Receiver accepted Frame {frame}, sequence {seq}"
                    )

                    ack_frame = frame
                    send_ack = True

                elif frame < receiver_expected:
                    # Duplicate: do not deliver it a second time.
                    record(
                        "receive",
                        frame,
                        f"Duplicate Frame {frame}, sequence {seq}"
                    )

                    # Repeat ACK to recover from ACK loss.
                    ack_frame = frame
                    send_ack = True

                else:
                    record(
                        "receive",
                        frame,
                        f"Unexpected Frame {frame} rejected"
                    )
                    send_ack = False

            elif is_sr:
                # Accept frames in the current receiver window.
                if (
                    receiver_expected
                    <= frame
                    < receiver_expected + window_size
                ):
                    first_arrival = frame not in received_frames
                    received_frames.add(frame)

                    while receiver_expected in received_frames:
                        receiver_expected += 1

                    record(
                        "receive",
                        frame,
                        f"Receiver accepted Frame {frame}"
                        if first_arrival
                        else f"Duplicate Frame {frame} received"
                    )

                    ack_frame = frame
                    send_ack = True

                elif frame in received_frames:
                    # Previously accepted duplicate.
                    record(
                        "receive",
                        frame,
                        f"Duplicate Frame {frame} received"
                    )

                    ack_frame = frame
                    send_ack = True

                else:
                    record(
                        "receive",
                        frame,
                        f"Frame {frame} rejected: outside receive window"
                    )
                    send_ack = False

            else:
                # Go-Back-N receiver accepts only the next expected frame.
                if frame == receiver_expected:
                    received_frames.add(frame)
                    receiver_expected += 1

                    record(
                        "receive",
                        frame,
                        f"Receiver accepted Frame {frame}"
                    )
                else:
                    record(
                        "receive",
                        frame,
                        f"Out-of-order or duplicate Frame {frame}"
                    )

                # Cumulative ACK: highest consecutive frame.
                ack_frame = receiver_expected - 1
                send_ack = True

            # ---------------- ACK TRANSMISSION ----------------

            if send_ack:
                if random.random() * 100 < ack_loss:
                    if is_one_bit:
                        record(
                            "ack_lost",
                            ack_frame,
                            f"ACK {sequence_number(ack_frame)} lost"
                        )
                    else:
                        record(
                            "ack_lost",
                            ack_frame,
                            f"ACK {ack_frame} lost"
                        )
                else:
                    schedule(
                        current_time + ack_delay,
                        "ack",
                        ack_frame
                    )

        # ==================================================
        # ACK ARRIVAL
        # ==================================================

        elif kind == "ack":

            stats["acks_received"] += 1
            old_base = base

            if is_one_bit:
                ack_seq = sequence_number(frame)

                record(
                    "ack",
                    frame,
                    f"ACK {ack_seq} received for Frame {frame}"
                )

                # Accept ACK only for the outstanding frame.
                if (
                    frame == base
                    and frame < next_frame
                    and frame not in acknowledged
                ):
                    acknowledged.add(frame)
                    invalidate_timer(frame)
                    base += 1

            elif is_sr:
                record("ack", frame, f"ACK {frame} received")

                if (
                    0 <= frame < next_frame
                    and frame not in acknowledged
                ):
                    acknowledged.add(frame)
                    invalidate_timer(frame)

                # IMPORTANT: slide SR sender base over all
                # consecutive acknowledged frames.
                while base < num_frames and base in acknowledged:
                    base += 1

            else:
                record("ack", frame, f"ACK {frame} received")

                # Go-Back-N cumulative ACK.
                if 0 <= frame < next_frame:
                    for f in range(frame + 1):
                        if f not in acknowledged:
                            acknowledged.add(f)
                            invalidate_timer(f)

                while base < num_frames and base in acknowledged:
                    base += 1

            # Restart GBN timer only if the base advanced.
            if is_gbn and base != old_base:
                if old_base < num_frames:
                    invalidate_timer(old_base)

                if base < next_frame and base < num_frames:
                    start_timer(base)

            # Send additional frames as the window advances.
            fill_window()

        # ==================================================
        # TIMEOUT
        # ==================================================

        elif kind == "timeout":

            if frame in acknowledged:
                continue

            if timer_generation[frame] != generation:
                continue

            if not timer_running[frame]:
                continue

            if is_gbn:
                if frame != base:
                    continue

                record(
                    "timeout",
                    frame,
                    f"Timeout for oldest outstanding Frame {frame}"
                )

                invalidate_timer(frame)

                # If the oldest outstanding frame has exhausted its retry
                # budget, stop instead of creating an endless timer loop.
                if attempts[base] >= max_attempts:
                    record(
                        "limit",
                        base,
                        f"Frame {base} reached retry limit; simulation stopped"
                    )
                    break

                # Retransmit all outstanding frames.
                for f in range(base, next_frame):
                    if f not in acknowledged:
                        send_frame(f)

                if (
                    base < next_frame
                    and base < num_frames
                    and attempts[base] < max_attempts
                ):
                    start_timer(base)

            elif is_sr:
                record(
                    "timeout",
                    frame,
                    f"Timeout for Frame {frame}"
                )

                invalidate_timer(frame)
                send_frame(frame)

            elif is_one_bit:
                if frame != base:
                    continue

                record(
                    "timeout",
                    frame,
                    f"Timeout for Frame {frame}, sequence {sequence_number(frame)}"
                )

                invalidate_timer(frame)
                send_frame(frame)

    # ---------------- FINAL METRICS ----------------

    delivered = len(acknowledged)
    total_time = current_time

    stats["successfully_delivered"] = delivered
    stats["total_time_ms"] = total_time

    stats["throughput_frames_per_second"] = (
        delivered * 1000 / total_time
        if total_time > 0 else 0
    )

    stats["efficiency_percent"] = (
        delivered * 100 / stats["total_frames_transmitted"]
        if stats["total_frames_transmitted"] > 0 else 0
    )

    stats["completed"] = delivered == num_frames

    record(
        "complete",
        None,
        "Simulation completed"
        if stats["completed"]
        else "Simulation stopped before all frames were acknowledged"
    )

    stats["event_log"] = event_log

    return stats
